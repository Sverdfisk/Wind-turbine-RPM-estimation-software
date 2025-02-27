import cv2 as cv
import numpy as np
from feed import feed


class BpmCascade(feed.RpmFromFeed):
    def __init__(self, **kwargs):
        # Assume self.quad is set here to define quadrant
        super().__init__(**kwargs)
        for key, value in kwargs.items():
            setattr(self, key, value)

        self.center = self.get_center_pixel()
        self.corner = self._get_quadrant_corner_pixel()
        self.hypotenuse_length = self.get_hypotenuse_length()

    # Uses mathematical quadrants, not OpenCV indexing
    def _get_quadrant_corner_pixel(self):
        list_index = quadrant - 1
        all_corners = [
            (self.w - 1, 0),  # Top right
            (0, 0),  # Top left
            (0, self.h - 1),  # Bottom left
            (self.w - 1, self.h - 1),  # Bottom right
        ]

        corner_pixel = all_corners[list_index]
        return corner_pixel

    def get_hypotenuse_length(self):
        xlen = abs(self.center[0] - self.corner[0])
        ylen = abs(self.center[1] - self.corner[1])
        hyp_length = sqrt((ylen**2) + (xlen**2))
        return hyp_length
