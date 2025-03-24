import cv2 as cv
import numpy as np
from . import calculate_rpm as crpm
from .feed import feed
import math
from collections import deque


class BoundingBox:
    """
    Wrapper class for bounding box sub-regions.
    Helps with instantiation of regions.

    Args:
        center (tuple): Coordinate specifying the centerpoint of the bounding box.
        size: (int): specifies the "radius" of the box.
        region (slice:slice): specifies a region (yslice, xslice) as an alternative to center coordinate + size

    """

    def __init__(self, center, size, region):
        self.center = center
        self.size = size

        #  Region in OpenCV crop format
        self.region = region
        #  side length =/= size
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
    """
    Wrapper class for blade detection mechanisms. Intended to be used in composition.

    Args:
        parent (class): The composition parent.

    """

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

    def calculate_rpm(self, frame_time: int, fps: float) -> float:
        return crpm.calculate_rpm_from_frame_time(frame_time, fps)


class Draw:
    """
    Wrapper class for drawing mehanisms and related utilities.

    Args:
        parent (class): The composition parent.

    """

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
        res = cv.addWeighted(subregion, base_weight, white_rect, draw_weight, 1.0)

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

    def processing_results(
        self, frame: np.ndarray, region: tuple[slice, slice], value: np.ndarray
    ) -> np.ndarray:
        frame[region] = value
        return frame

    def border_around_region(self, image: np.ndarray, thickness: int, color: list[int]):
        h, w = image.shape[:2]
        cv.rectangle(
            image,
            (0, 0),
            (w - 1, h - 1),
            color,
            thickness=thickness,
        )
        return image


class FrameBuffer:
    """
    A wrapper class for initialized deques. Contains methods that simplify the trivial stuff.

    Args:
        parent (class): The composition parent.

    """

    def __init__(self, parent):
        self.parent = parent
        self.average_delta = 0

    def insert(self, buffer: int, region: np.ndarray) -> None:
        # Store the processed regions and nice-to-haves in the buffer
        intensity = int(round(np.mean(region)))

        if len(self.parent.frame_buffers[buffer]) > 0:
            prev_frame_intensity = self.parent.frame_buffers[buffer][-1]["intensity"]
        else:
            #  Just to keep the delta at 0 to avoid startup spikes
            prev_frame_intensity = intensity
        intensity_delta = intensity - prev_frame_intensity
        # print(f"buffer: {buffer} - delta: {intensity_delta}")

        entry = {
            "subregion": region,
            "intensity": intensity,
            "intensity_delta": intensity_delta,
        }
        self.parent.frame_buffers[buffer].append(entry)

    # Only takes the last updated value and updates avgs
    # Designed this way so a user can conditionally update
    def update_averages(self) -> None:
        vals = []
        for fb in self.parent.frame_buffers:
            for entry in fb:
                vals.append(entry["intensity_delta"])
        self.average_delta = round(np.mean(vals))


class BpmCascade(feed.RpmFromFeed):
    """
    The main class. Contains and/or utilizes the other classes in some way or another.
    "Cascades" bounding boxes; meaning that it contains logic for repeating N boxes
    as separate detection regions. Contains logic for managing these regions.

    Args:
        **kwargs (dict from JSON-config file): see software/config/config_template.json.

    """

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
        self.fb = FrameBuffer(self)
        self.quadrant: int
        self.stack_boxes_vertically: bool
        self.stack_boxes_horizontally: bool
        self.trim_last_n_boxes: int
        self.box_start_index: int

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

    def print_useful_stats(self, out: list, frame_ticks: deque, toggle: bool) -> None:
        print(
            f"frame: {self.frame_cnt} - color diff: {
                self.fb.average_delta
            } - detect enabled: {toggle} - latest measured RPM: {
                0 if out == [] else round(out[-1], 1)
            } - last detection at: {
                None if frame_ticks == deque(maxlen=2) else frame_ticks[-1]
            }"
        )

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
        # In the horizontal or vertical stacking cases,
        # using the radius to the middle of a box's side
        # is better

        box_diameter = 2 * box_size
        if self.stack_boxes_vertically:
            num_boxes = math.floor(self.radius_y / box_diameter)
            return num_boxes
        elif self.stack_boxes_horizontally:
            num_boxes = math.floor(self.radius_x / box_diameter)
            return num_boxes

        # Diagonal case
        else:
            box_diagonal = round(2 * box_size * math.sqrt(2))
            num_boxes = math.floor(self.hypotenuse_length / box_diagonal)
            return num_boxes

    def fit_box_parameters_to_radius(
        self,
        wanted_num_boxes: int,
        wanted_box_size: int,
        resize_boxes: bool = False,
        adjust_num_boxes: bool = False,
    ) -> tuple[int, int]:
        # Calculate how many boxes can fit with the current box size:
        initial_box_limit = self.boxes_in_radius(wanted_box_size)

        # Initialize as an ideal request
        result_boxes = wanted_num_boxes
        result_size = wanted_box_size

        # Case 1: The current request goes out of bounds (too many boxes for the size).
        if wanted_num_boxes > initial_box_limit:
            if adjust_num_boxes:
                # Instead of resizing, adjust the box count to the maximum available.
                result_boxes = initial_box_limit

            elif resize_boxes:
                # Reduce the box size until it can hold the desired number of boxes.
                while True:
                    if self.boxes_in_radius(result_size) < wanted_num_boxes:
                        result_size -= 1
                    else:
                        break

        # Case 2: The user is within bounds.
        else:
            if resize_boxes:
                # Expand box size until increasing it further would mean we are out of bounds
                while True:
                    if self.boxes_in_radius(result_size + 1) <= initial_box_limit:
                        result_size += 1
                    else:
                        break

            elif adjust_num_boxes:
                # We are within bounds, and we can just set the number of boxes to be the max
                result_boxes = initial_box_limit

        return (result_boxes, result_size)

    def _initialize_frame_buffers(
        self, num_buffers: int, frame_buffer_length: int
    ) -> None:
        self.frame_buffers = []
        self.frame_buffer_averages = []
        for _ in range(num_buffers):
            self.frame_buffers.append(deque(maxlen=frame_buffer_length))

    def cascade_bounding_boxes(
        self,
        num_boxes: int,
        box_size,
        frame_buffer_size: int = 5,
    ) -> list[BoundingBox]:
        bounds = []
        self._initialize_frame_buffers(num_boxes, frame_buffer_size)

        #  TODO: figure out a smarter way to do this axis stuff
        delta_y = (
            0
            if self.stack_boxes_horizontally
            else box_size * (2 * self.quadrant_axis_map[1])
        )
        delta_x = (
            0
            if self.stack_boxes_vertically
            else box_size * (2 * self.quadrant_axis_map[0])
        )

        offset_y = (
            self.corner[1]
            - self.center_of_frame[1]
            + (box_size * self.quadrant_axis_map[1] - 1)
        )
        offset_x = (
            self.corner[0]
            - self.center_of_frame[0]
            + (box_size * self.quadrant_axis_map[0])
        )

        box_range = slice(self.box_start_index, num_boxes - self.trim_last_n_boxes)
        for i in range(box_range.start, box_range.stop):
            box_x = round(offset_x + delta_x * i)
            box_y = round(offset_y + delta_y * i)
            box_center = (box_x, box_y)
            bounds.append(BoundingBox.from_center_and_size(box_center, box_size))
        return bounds
