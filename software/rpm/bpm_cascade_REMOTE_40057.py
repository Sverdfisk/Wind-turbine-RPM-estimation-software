import cv2 as cv
import numpy as np
from .feed import feed
import math


class BoundingBox:
    def __init__(self, center, size, region):
        self.center = center
        self.size = size

        #  Region in OpenCV crop format
        self.region = region
        #  size from center or "radius"
        self.side_length = self.size * 2

    def area(self):
        return self.side_length * self.side_length

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
        sizex = (xrange.stop - yrange.start) // 2
        assert sizey == sizex  # Force square size
        center = ((xrange.start + sizex), (yrange.start + sizey))
        return (center, sizex)


class Draw:
    def __init__(self, parent):
        self.parent = parent

    def draw_opaque_region(
        self,
        base_frame: np.ndarray,
        draw_region: tuple[slice, slice],
        w1: float,
        w2: float,
    ) -> np.ndarray:
        yrange, xrange = draw_region

        subregion = base_frame[yrange, xrange]
        white_rect = np.ones(subregion.shape, dtype=np.uint8) * 255
        res = cv.addWeighted(subregion, w1, white_rect, w2, 1.0)

        base_frame[yrange, xrange] = res
        return base_frame

    def draw_active_quadrant(self, base_frame: np.ndarray) -> np.ndarray:
        marked_quadrant = self.draw_opaque_region(
            base_frame, self.parent.quadrant_subsection, 0.7, 0.3
        )
        return marked_quadrant

    def draw_marker_box(
        self, base_frame: np.ndarray, center: tuple[int, int], size: int
    ) -> np.ndarray:
        yrange = slice(center[1] - size, center[1] + size)
        xrange = slice(center[0] - size, center[0] + size)
        new_frame = self.draw_opaque_region(base_frame, (yrange, xrange), 0.7, 0.3)
        return new_frame


class BpmCascade(feed.RpmFromFeed):
    def __init__(self, **kwargs):
        # Assume self.quadrant is set here to define quadrant
        super().__init__(**kwargs)
        for key, value in kwargs.items():
            setattr(self, key, value)
        self.center_of_frame = self.get_center_pixel()
        self.corner = self._get_quadrant_corner_pixel(self.quadrant)
        self.hypotenuse_length = self._get_hypotenuse_length()
        self.quadrant_subsection = self._get_quadrant_subsection_slice()
        self.bounds = self.cascade_bounding_boxes(1, 5)
        self.draw = Draw(self)

    # Uses mathematical quadrants, not OpenCV indexing
    def _get_quadrant_corner_pixel(self, quadrant: int) -> tuple[int, int]:
        list_index = quadrant - 1
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
        box_diagonal = round(box_size * math.sqrt(2))
        num_boxes = math.floor(self.hypotenuse_length / box_diagonal)
        return num_boxes

    def cascade_bounding_boxes(self, num_boxes: int, box_size) -> list[BoundingBox]:
        box_center = tuple(coord + box_size for coord in self.center_of_frame)
        bounds = BoundingBox(
            box_center,
            box_size,
            BoundingBox.region_from_center_and_size(box_center, box_size),
        )
        return bounds
