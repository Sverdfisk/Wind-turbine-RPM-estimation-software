import cv2 as cv
import numpy as np
from feed import feed
import math


class BpmCascade(feed.RpmFromFeed):
    def __init__(self, **kwargs):
        # Assume self.quadrant is set here to define quadrant
        super().__init__(**kwargs)
        for key, value in kwargs.items():
            setattr(self, key, value)

        self.center = self.get_center_pixel()
        self.corner = self._get_quadrant_corner_pixel(self.quadrant)
        self.hypotenuse_length = self._get_hypotenuse_length()
        self.subsection = self._get_quadrant_subsection_slice()

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
            xrange = slice(self.corner[0], self.center[0])
        else:
            xrange = slice(self.center[0], self.corner[0])

        if (self.quadrant == 1) or (self.quadrant == 2):
            yrange = slice(self.corner[1], self.center[1])
        else:
            yrange = slice(self.center[1], self.corner[1])

        return (yrange, xrange)

    def _get_hypotenuse_length(self) -> float:
        xlen = abs(self.center[0] - self.corner[0])
        ylen = abs(self.center[1] - self.corner[1])
        hyp_length = math.sqrt((ylen**2) + (xlen**2))
        return hyp_length

    def draw_opaque_region(self, base_frame: np.ndarray, draw_region: tuple[slice, slice], w1: float, w2: float):
        yrange, xrange = range

        subregion = base_frame[yrange, xrange]
        white_rect = np.ones(subregion.shape, dtype=np.uint8) * 255
        res = cv2.addWeighted(subregion, w1, white_rect, w2, 1.0)

        base_frame[yrange, xrange] = res
        return base_frame

    def draw_active_quadrant(self, base_frame: np.ndarray) -> np.ndarray:
        quadrant_range = self._get_quadrant_subsection_slice()
        marked_quadrant = self.draw_opaque_region(
            base_frame, quadrant_range, 0.7, 0.3)
        return marked_quadrant

    def draw_marker_box(self, base_frame: np.ndarray, center: tuple[int, int], size: int) -> np.ndarray:
