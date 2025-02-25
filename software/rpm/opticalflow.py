import numpy as np
import cv2 as cv
import math
from . import calculate_rpm as crpm


class RpmFromFeed:
    def __init__(self, threshold=10, mask="circle", **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

        # Video feed settings
        self.feed = cv.VideoCapture(kwargs["target"])
        self.feed.set(cv.CAP_PROP_FPS, self.fps)

        # Set image frame parameters
        if self.crop_points is not None and (
            self.crop_points[0][1] - self.crop_points[0][0]
        ) == (self.crop_points[1][1] - self.crop_points[1][0]):
            self.shape = "SQUARE"
        else:
            self.shape = "RECT"
        self.old_frame = self._set_initial_frame(self.ground_angle)
        self.set_mask_size()
        self.radius = int(math.sqrt(self.radius_x * self.radius_y))

        # Algorithm config
        self.st_params = self.set_shi_tomasi_params()
        self.lk_params = self.set_lucas_kanade_params()
        self.set_deadzone_size(self.deadzone_size)
        if mask == "circle":
            deadzone_radius = int(
                math.sqrt(self.deadzone_size[0] * self.deadzone_size[1])
            )
            self.feature_mask = self.generate_circular_feature_mask_matrix(
                self.old_frame,
                self.deadzone_offset_x,
                self.deadzone_offset_y,
                deadzone_radius,
            )
        else:
            self.feature_mask = self.generate_feature_mask_matrix(
                self.old_frame, self.deadzone_offset_x, self.deadzone_offset_y
            )

        # Control config
        self.isActive = True

        # Sets tracking point threshold, i.e acceptable tracking distance. A reasonable range is 0 to about 60  (10 is strict).
        # lower threshold -> better confidence is needed to set a correlation as "successful".
        # higher threshold -> More options for pixels that could be the one we track. Noisy, but more data.
        self.threshold = threshold

        # Color for drawing purposes
        self.color = np.random.randint(0, 255, (100, 3))

    def set_perspective_parameters(self, ground_angle):
        # Do a whole lot of trig to correct for persepective
        hypotenuse = self.h if (self.h > self.w) else self.w
        adjacent = self.w if (self.h > self.w) else self.h
        perspective_rotation_angle = math.acos(adjacent / hypotenuse)

        self.rpm_scaling_factor = crpm.view_angle_scaling(
            ground_angle, perspective_rotation_angle
        )
        # Squareify the image to somewhat un-distort perspective
        pts_src = np.float32(
            [
                [0, 0],  # top-left
                [self.w - 1, 0],  # top-right
                [self.w - 1, self.h - 1],  # bottom-right
                [0, self.h - 1],
            ]
        )  # bottom-left

        new_h = self.h if (self.h > self.w) else self.w
        pts_dst = np.float32(
            [
                [0, 0],  # top-left in the new image
                [new_h, 0],  # top-right in the new image
                [new_h, new_h],  # bottom-right in the new image
                [0, new_h],
            ]
        )  # bottom-left in the new image

        self.translation_matrix = cv.getPerspectiveTransform(pts_src, pts_dst)

    def _correct_frame_perspective(self, frame):
        warped = cv.warpPerspective(
            frame, self.translation_matrix, (self.h, self.h))
        return warped

    def set_deadzone_size(self, size):
        if size is not None:
            self.deadzone_size_x, self.deadzone_size_y = size
        else:
            pass

    def set_mask_size(self):
        self.mask = np.zeros_like(self.old_frame)

    def set_shi_tomasi_params(
        self, maxCorners=100, qualityLevel=0.05, minDistance=9, blockSize=3
    ) -> dict:
        params = dict(
            maxCorners=maxCorners,
            qualityLevel=qualityLevel,
            minDistance=minDistance,
            blockSize=blockSize,
        )
        return params

    def set_lucas_kanade_params(
        self,
        winSize=(15, 15),
        maxLevel=2,
        criteria=(cv.TERM_CRITERIA_EPS | cv.TERM_CRITERIA_COUNT, 10, 0.03),
    ) -> dict:
        params = dict(winSize=winSize, maxLevel=maxLevel, criteria=criteria)
        return params

    def translate_coords_to_centre(
        self, image_height: int, image_width: int, sizex: int = 0, sizey: int = 0
    ) -> list:
        centre = [image_height / 2, image_width / 2]
        x_left = int(centre[1] - sizex)
        x_right = int(centre[1] + sizex)
        y_top = int(centre[0] - sizey)
        y_bottom = int(centre[0] + sizey)
        return [x_left, x_right, y_top, y_bottom]

    def generate_feature_mask_matrix(
        self, image: np.ndarray, deadzone_offset_x, deadzone_offset_y
    ) -> np.ndarray:
        size = [self.deadzone_size_x, self.deadzone_size_y]
        height, width, channels = image.shape
        mask = np.full((height, width), 255, dtype=np.uint8)
        x_left, x_right, y_top, y_bottom = self.translate_coords_to_centre(
            height, width, sizex=size[0], sizey=size[1]
        )
        self.maskpoints = [
            (x_left + deadzone_offset_x),
            (x_right + deadzone_offset_x),
            (y_top + deadzone_offset_y),
            (y_bottom + deadzone_offset_y),
        ]
        mask[
            (y_top + deadzone_offset_y): (y_bottom + deadzone_offset_y),
            (x_left + deadzone_offset_x): (x_right + deadzone_offset_x),
        ] = 0
        return mask

    def generate_circular_feature_mask_matrix(
        self,
        image: np.ndarray,
        deadzone_offset_x: int,
        deadzone_offset_y: int,
        radius: int,
    ):
        h, w, ch = image.shape
        mask = np.full((h, w), 255, dtype=np.uint8)

        radius_y = int(h / 2) + deadzone_offset_y
        radius_x = int(w / 2) + deadzone_offset_x

        self.maskpoints = [
            int(w / 2) - radius,
            int(w / 2) + radius,
            int(h / 2) - radius,
            int(h / 2) + radius,
        ]
        cv.circle(mask, (radius_x, radius_y), radius, (0, 0, 0), -1)
        return mask

    def _set_initial_frame(self, ground_angle) -> np.ndarray:
        ret, frame = self.feed.read()
        if (self.crop_points is not None) and ret:
            frame = frame[
                self.crop_points[0][0]: self.crop_points[0][1],
                self.crop_points[1][0]: self.crop_points[1][1],
            ]

        self.h, self.w, self.ch = frame.shape
        self.set_perspective_parameters(ground_angle)
        self.isActive = ret

        if self.shape == "RECT":
            frame = self._correct_frame_perspective(frame)
        return frame

    def get_frame(self) -> np.ndarray:
        ret, frame = self.feed.read()
        self.isActive = ret

        if (self.crop_points is not None) and ret:
            frame = frame[
                self.crop_points[0][0]: self.crop_points[0][1],
                self.crop_points[1][0]: self.crop_points[1][1],
            ]

        if self.shape == "RECT" and ret:
            frame = self._correct_frame_perspective(frame)

        return frame if ret else np.zeros_like(frame)

    def calculate_rpm_from_vectors(self, motion_vectors):
        radius_max = self.radius_y if (
            self.radius_y > self.radius_x) else self.radius_x
        return crpm.get_rpm(motion_vectors, radius_max, self.fps)

    def draw_optical_flow(
        self, image: np.ndarray, old_points: list, new_points: list, overwrite=False
    ) -> np.ndarray:
        if overwrite:
            self.mask = np.zeros_like(image)

        for i, (new, old) in enumerate(zip(new_points, old_points)):
            a, b = new.ravel()
            c, d = old.ravel()
            self.mask = cv.line(
                self.mask, (int(a), int(b)), (int(c), int(d)
                                              ), self.color[i].tolist(), 2
            )
            image = cv.circle(image, (int(a), int(b)), 5,
                              self.color[i].tolist(), -1)

        # Draws the boundaries for the deadzone (feature mask) if it's square
        red = [0, 0, 255]
        fromx, tox, fromy, toy = self.maskpoints
        cv.circle(self.mask, (fromx, toy), 4, red, -1)
        cv.circle(self.mask, (fromx, fromy), 4, red, -1)
        cv.circle(self.mask, (tox, fromy), 4, red, -1)
        cv.circle(self.mask, (tox, toy), 4, red, -1)

        return cv.add(self.mask, image)

    def get_optical_flow_vectors(self) -> tuple:
        old_frame_gray = cv.cvtColor(self.old_frame, cv.COLOR_BGR2GRAY)
        new_frame = self.get_frame()
        if not self.isActive:
            return (None, None)

        new_frame_gray = cv.cvtColor(new_frame, cv.COLOR_BGR2GRAY)

        # find features in our old grayscale frame. feature mask is dynamic but manual
        p0 = cv.goodFeaturesToTrack(
            old_frame_gray, mask=self.feature_mask, **self.st_params
        )
        p1, st, err = cv.calcOpticalFlowPyrLK(
            old_frame_gray, new_frame_gray, p0, None, **self.lk_params
        )

        # Select good tracking points based on successful tracking
        if p1 is not None:
            good_new = p1[(st == 1) & (abs(err) < self.threshold)]
            good_old = p0[(st == 1) & (abs(err) < self.threshold)]

        # Set the new frame to be considered "old" for next call
        self.old_frame = new_frame

        return (good_new, good_old), new_frame
