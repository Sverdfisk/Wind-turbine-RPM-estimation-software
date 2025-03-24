import cv2 as cv
import numpy as np


class Feed:
    def __init__(self, **kwargs):
        self.crop_points = kwargs["crop_points"]
        self.frame_cnt = 0
        self._set_base_config(kwargs["target"], kwargs["fps"])

    def _set_base_config(self, target, fps) -> None:
        self.target = target
        self.fps = fps
        self.video = cv.VideoCapture(self.target)
        self.video.set(cv.CAP_PROP_FPS, self.fps)
        if self.crop_points is not None:
            self.h = self.crop_points[0][1] - self.crop_points[0][0]
            self.w = self.crop_points[1][1] - self.crop_points[1][0]
            self.yrange = slice(self.crop_points[0][0], self.crop_points[0][1])
            self.xrange = slice(self.crop_points[1][0], self.crop_points[1][1])
        else:
            img = self.get_frame()
            self.h, self.w, self.ch = img.shape
            self.yrange = slice(0, self.h)
            self.xrange = slice(0, self.w)

    def get_frame(self) -> np.ndarray:
        ret, frame = self.video.read()
        self.isActive = ret
        if ret:
            self.frame_cnt += 1
        if self.crop_points is not None and ret:
            frame = frame[self.yrange, self.xrange]
        return frame


class RpmFromFeed(Feed):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._set_config_parameters(kwargs["crop_points"])

    def _set_config_parameters(self, crop_points) -> None:
        self.crop_points = crop_points

        self.radius_x = self.w // 2
        self.radius_y = self.h // 2
        if self.radius_x > self.radius_y:
            self.radius_max = self.radius_x
        else:
            self.radius_max = self.radius_y

        if (crop_points is not None) and (self.w == self.h):
            self.shape = "SQUARE"
        else:
            self.shape = "RECT"

    def get_center_pixel(self) -> tuple:
        # We can just use the radius here to find the middle of the image
        return (self.radius_y, self.radius_x)
