import cv2 as cv
import numpy as np
from .feed import feed
import math
from collections import deque


class BoundingBox:
    def __init__(self, center, size, region):
        self.center = center
        self.size = size

        #  Region in OpenCV crop format
        self.region = region
        #  size from center or "radius"
        self.side_length = self.size * 2
        self.draw = Draw(self)
        self.detect_blade = DetectBlade(self)

    def area(self):
        return self.side_length * self.side_length

    @classmethod
    def from_center_and_size(cls, center, size):
        region = cls.region_from_center_and_size(center, size)
        return cls(center, size, region)

    @classmethod
    def from_region(cls, region):
        center, size = cls.center_and_size_from_region(region)
        return cls(center, size, region)

    @staticmethod
    def region_from_center_and_size(
        center: tuple[int, int], size: int
    ) -> tuple[slice, slice]:
        yrange = slice(center[1] - size, center[1] + size)
        xrange = slice(center[0] - size, center[0] + size)
        return (yrange, xrange)

    @staticmethod
    def center_and_size_from_region(
        region: tuple[slice, slice],
    ) -> tuple[tuple[int, int], int]:
        yrange = region[0]
        xrange = region[1]
        sizey = (yrange.stop - yrange.start) // 2
        sizex = (xrange.stop - xrange.start) // 2
        assert sizey == sizex  # Force square size
        center = ((xrange.start + sizex), (yrange.start + sizey))
        return (center, sizex)


class DetectBlade:
    def __init__(self, parent):
        self.parent = parent

    # Returns an array of altered pixels in its own region
    def dilation_erosion(
        self,
        frame: np.ndarray,
        kernel_size: tuple[int, int],
        dil_it: int,
        er_it: int,
    ) -> np.ndarray:
        subregion = frame[self.parent.region]
        kernel = cv.getStructuringElement(cv.MORPH_RECT, kernel_size)
        dilated = cv.dilate(subregion, kernel, dil_it)
        processed_subregion = cv.erode(dilated, kernel, er_it)
        return processed_subregion


class Draw:
    def __init__(self, parent):
        self.parent = parent

    def opaque_region(
        self,
        base_frame: np.ndarray,
        draw_region: tuple[slice, slice],
        base_weight: float,
        draw_weight: float,
    ) -> np.ndarray:
        yrange, xrange = draw_region
        subregion = base_frame[yrange, xrange]
        white_rect = np.ones(subregion.shape, dtype=np.uint8) * 255
        res = cv.addWeighted(subregion, base_weight,
                             white_rect, draw_weight, 1.0)

        base_frame[yrange, xrange] = res
        return base_frame

    def active_quadrant(
        self, base_frame: np.ndarray, base_weight: float, draw_weight: float
    ) -> np.ndarray:
        marked_quadrant = self.opaque_region(
            base_frame, self.parent.quadrant_subsection, base_weight, draw_weight
        )
        return marked_quadrant

    def bounding_box(
        self,
        base_frame: np.ndarray,
        box: BoundingBox,
        base_weight: float,
        draw_weight: float,
    ) -> np.ndarray:
        yrange = slice(box.center[1] - box.size, box.center[1] + box.size)
        xrange = slice(box.center[0] - box.size, box.center[0] + box.size)
        new_frame = self.opaque_region(
            base_frame, (yrange, xrange), base_weight, draw_weight
        )
        return new_frame

    def processing_results(self, frame: np.ndarray, value: np.ndarray) -> np.ndarray:
        frame[self.parent.region] = value
        return frame


class BpmCascade(feed.RpmFromFeed):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        for key, value in kwargs.items():
            setattr(self, key, value)
        self.center_of_frame = self.get_center_pixel()
        self.corner = self._get_quadrant_corner_pixel()
        self.hypotenuse_length = self._get_hypotenuse_length()
        self.quadrant_subsection = self._get_quadrant_subsection_slice()
        self.quadrant_axis_map = self._generate_axis_mapping()
        self.draw = Draw(self)

    def _generate_axis_mapping(self) -> tuple[int, int]:
        axes = (1, -1)
        if self.quadrant == 2:
            axes = (-1, -1)
        elif self.quadrant == 3:
            axes = (-1, 1)
        elif self.quadrant == 4:
            axes = (1, 1)
        return axes

    # Uses mathematical quadrants, not OpenCV indexing
    def _get_quadrant_corner_pixel(self) -> tuple[int, int]:
        list_index = self.quadrant - 1
        all_corners = [
            (self.w - 1, 0),  # Top right
            (0, 0),  # Top left
            (0, self.h - 1),  # Bottom left
            (self.w - 1, self.h - 1),  # Bottom right
        ]

        corner_pixel = all_corners[list_index]
        return corner_pixel

    def _get_quadrant_subsection_slice(self) -> tuple[slice, slice]:
        #  This is hardcoded and absolutely awful. I'm sorry
        #  The slice bounds are absolute, while the quadrants
        #  are relative to the center.
        if (self.quadrant == 2) or (self.quadrant == 3):
            xrange = slice(self.corner[0], self.center_of_frame[0])
        else:
            xrange = slice(self.center_of_frame[0], self.corner[0])

        if (self.quadrant == 1) or (self.quadrant == 2):
            yrange = slice(self.corner[1], self.center_of_frame[1])
        else:
            yrange = slice(self.center_of_frame[1], self.corner[1])

        return (yrange, xrange)

    def _get_hypotenuse_length(self) -> float:
        xlen = abs(self.center_of_frame[0] - self.corner[0])
        ylen = abs(self.center_of_frame[1] - self.corner[1])
        hyp_length = math.sqrt((ylen**2) + (xlen**2))
        return hyp_length

    def boxes_in_radius(self, box_size: int) -> int:
        box_diagonal = round(2 * box_size * math.sqrt(2))
        num_boxes = math.floor(self.hypotenuse_length / box_diagonal)
        return num_boxes

    # TODO: implement this. Supposed to readjust box number and size parameters
    # to make them fit within the frame, avoiding crashes
    def fit_box_parameters_to_radius(
        self,
        wanted_box_size: int,
        wanted_num_boxes: int,
        resize_boxes: bool = True,
        adjust_num_boxes: bool = False,
    ) -> tuple[int, int]:
        # Calculate how many boxes can fit with the current box size:
        box_limit = self.boxes_in_radius(wanted_box_size)

        # Initialize as an ideal request
        result_boxes = wanted_num_boxes
        result_size = wanted_box_size

        # Case 1: The current request goes out of bounds
        if wanted_num_boxes > box_limit:
            if adjust_num_boxes:
                # The current limit finder always undershoots, so this is safe
                result_boxes = box_limit  # - 1

            elif resize_boxes:
                # Reduce the box size until it can hold the desired box count
                while True:
                    result_size -= 1
                    new_box_amount = self.boxes_in_radius(result_size)
                    if new_box_amount <= wanted_num_boxes:
                        break

        # Case B: The user is within bounds
        else:
            # 1) If set, expand box size to the largest possible until it no longer fits
            if resize_boxes:
                while True:
                    if self.boxes_in_radius(result_size) < wanted_num_boxes:
                        break
                    result_size += 1

            # 2) If set, increase the number of boxes until adding one more goes out of bounds
            if adjust_num_boxes:
                while True:
                    if self.boxes_in_radius(result_size) >= result_boxes:
                        break
                    result_boxes += 1

        # Store the final ‘safe’ parameters
        return (result_boxes, result_size)

    def _initialize_queues(self, num_queues: int, queue_length: int) -> None:
        self.frame_buffers = []
        for i in range(num_queues):
            self.frame_buffers.append(deque(maxlen=queue_length))

    def cascade_bounding_boxes(
        self, num_boxes: int, box_size, queue_length: int = 5
    ) -> list[BoundingBox]:
        bounds = []
        self._initialize_queues(num_boxes, queue_length)
        #  TODO: figure out a smarter way to do this axis stuff
        offset_y = (
            self.corner[1]
            - self.center_of_frame[1]
            + (box_size * self.quadrant_axis_map[1] - 1)
        )
        delta_y = box_size * (2 * self.quadrant_axis_map[1])

        offset_x = (
            self.corner[0]
            - self.center_of_frame[0]
            + (box_size * self.quadrant_axis_map[0])
        )
        delta_x = box_size * (2 * self.quadrant_axis_map[0])

        for i in range(num_boxes):
            box_x = round(offset_x + delta_x * i)
            box_y = round(offset_y + delta_y * i)
            box_center = (box_x, box_y)
            bounds.append(BoundingBox.from_center_and_size(
                box_center, box_size))

        return bounds
