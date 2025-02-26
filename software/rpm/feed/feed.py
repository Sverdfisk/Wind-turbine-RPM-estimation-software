import numpy as numpy
import cv2 as cv


class Feed:
    def __init__(self, **kwargs):
        _set_base_config(kwargs["target"], kwargs["fps"])
        _set_frame_parameters(
            kwargs["crop_points"], kwargs["radius_x"], kwargs["radius_y"]
        )

    def _set_base_config(target, fps):
        self.target = target
        self.fps = fps
        self.video = cv.VideoCapture(self.target)
        self.video.set(cv.CAP_PROP_FPS, self.fps)

    def get_frame(self) -> np.ndarray:
        ret, frame = self.feed.read()
        if self.crop_points is not None and ret:
            frame = frame[self.xrange, self.yrange]
        return frame


class RpmFromFeed(Feed):
    def __init__(self, **kwargs):
        self._set_config_parameters

    def _set_config_parameters(crop_points, radius_x, radius_y):
        self.crop_points = crop_points

        self.radius_x = radius_x
        self.radius_y = radius_y
        if radius_x > radius_y:
            self.radius_max = radius_x
        else:
            self.radius_max = radius_y

        self.h = crop_points[0][1] - crop_points[0][0]
        self.w = crop_points[1][1] - crop_points[1][0]
        self.xrange = slice(crop_points[0][0], crop_points[0][1])
        self.yrange = slice(crop_points[1][0], crop_points[1][1])

        if (crop_points is not None) and (self.w == self.h):
            self.shape = "SQUARE"
        else:
            self.shape = "RECT"

        self.radius = int(math.sqrt(radius_x * radius_y))
