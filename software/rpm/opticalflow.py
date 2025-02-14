import numpy as np
import cv2 as cv
import math

class opticalflow():
    def __init__(self, video_feed_path, crop_points = None, crosshair_size = [15,15], fps=30, threshold = 10, crosshair_offset_x = 0, crosshair_offset_y = 0):

        #Video feed settings
        self.feed = cv.VideoCapture(video_feed_path)
        self.fps = fps
        self.feed.set(cv.CAP_PROP_FPS, self.fps)
        self.crop_points = crop_points

        # Set image frame parameters
        if ((crop_points[0][1] - crop_points[0][0]) == (crop_points[1][1] - crop_points[1][0])):
            self.shape = 'SQUARE'
        else:
            self.shape = 'ELLIPSE'

        self.old_frame = self.set_initial_frame()
        self.set_mask_size()

        #Algorithm config
        self.st_params = self.set_shi_tomasi_params()
        self.lk_params = self.set_lucas_kanade_params()
        self.set_crosshair_size(crosshair_size)
        self.feature_mask = self.generate_feature_mask_matrix(self.old_frame, crosshair_offset_x, crosshair_offset_y)

        #Control config
        self.isActive = True

        # Sets tracking point threshold. A reasonable range is 0 to about 60  (10 is strict).
        # lower threshold -> better confidence is needed to set a correlation as "successful".
        # higher threshold -> More options for pixels that could be the one we track. Noisy, but more data.
        self.threshold = threshold 

        #Color for drawing purposes
        self.color = np.random.randint(0, 255, (100, 3))

    def set_perspective_parameters(self):
        
        # Do a whole lot of trig to correct for persepective
        hypotenuse = self.h if (self.h > self.w) else self.w
        adjacent = self.w if (self.h > self.w) else self.h
        perspective_angle = math.acos(adjacent/hypotenuse)

        #TODO: THIS HAS TO BE DYNAMIC!!!
        ground_looking_up_const = 0.21 # radians

        # Find the plane normal vector of the turbine
        nx = math.cos(ground_looking_up_const) * math.sin(perspective_angle)
        ny = math.cos(ground_looking_up_const) * math.cos(perspective_angle)
        nz = math.sin(ground_looking_up_const)
        self.turbine_normal = np.array([nx, ny, nz])
        self.viewing_angle = np.array([0, 1, 0])

        # Find the scaling factor of the measurements
        angle_scale = np.dot(self.turbine_normal, self.viewing_angle)
        self.rpm_scaling_factor = 1 / angle_scale
        
        # Squareify the image to somewhat un-distort perspective 
        pts_src = np.float32([[0         , 0         ],   # top-left
                              [self.w - 1, 0         ],   # top-right
                              [self.w - 1, self.h - 1],   # bottom-right
                              [0         , self.h - 1]])  # bottom-left


        new_h = int(hypotenuse/0.98)
        pts_dst = np.float32([[0         , 0         ],  # top-left in the new image
                              [new_h, 0         ],  # top-right in the new image
                              [new_h, new_h],  # bottom-right in the new image
                              [0         , new_h]]) # bottom-left in the new image

        self.translation_matrix = cv.getPerspectiveTransform(pts_src, pts_dst)

    def correct_frame_perspective(self, frame):
        warped = cv.warpPerspective(frame, self.translation_matrix, (self.h, self.h))
        return warped

    def set_crosshair_size(self, size):
        if size is not None:
            self.crosshair_size_x, self.crosshair_size_y = size
        else:
            pass

    def set_mask_size(self):
        self.mask = np.zeros_like(self.old_frame)    

    def set_shi_tomasi_params(self, maxCorners = 100, 
                              qualityLevel = 0.05, 
                              minDistance = 9, 
                              blockSize = 3) -> dict:
        
        params = dict(maxCorners = maxCorners, 
                      qualityLevel = qualityLevel, 
                      minDistance = minDistance, 
                      blockSize = blockSize)
        return params

    def set_lucas_kanade_params(self, winSize = (15, 15), 
                                maxLevel = 2, 
                                criteria = (cv.TERM_CRITERIA_EPS | cv.TERM_CRITERIA_COUNT, 10, 0.03)) -> dict:

        params = dict(winSize = winSize, 
                      maxLevel = maxLevel, 
                      criteria = criteria)
        return params

    def translate_coords_to_centre(self, image_height: int, image_width: int, sizex: int = 0, sizey: int = 0) -> list:
        centre = [image_height/2, image_width/2]
        x_left = int(centre[1]-sizex)
        x_right = int(centre[1]+sizex)
        y_top = int(centre[0]-sizey)
        y_bottom = int(centre[0]+sizey)
        return [x_left, x_right, y_top, y_bottom]

    def generate_feature_mask_matrix(self, image: np.ndarray, crosshair_offset_x, crosshair_offset_y) -> np.ndarray:
        size = [self.crosshair_size_x, self.crosshair_size_y]
        height, width, channels = image.shape
        mask = np.full((height, width), 255, dtype=np.uint8)
        x_left, x_right, y_top, y_bottom = self.translate_coords_to_centre(height, width, sizex = size[0], sizey = size[1])
        self.maskpoints = [(x_left + crosshair_offset_x), (x_right + crosshair_offset_x), (y_top + crosshair_offset_y), (y_bottom + crosshair_offset_y)]
        mask[(y_top + crosshair_offset_y):(y_bottom + crosshair_offset_y), (x_left + crosshair_offset_x):(x_right + crosshair_offset_x)] = 0
        return mask

    def set_initial_frame(self) -> np.ndarray:
        ret, frame = self.feed.read()
        if (self.crop_points is not None) and ret:
            frame = frame[self.crop_points[0][0]:self.crop_points[0][1], 
                          self.crop_points[1][0]:self.crop_points[1][1]]
            
        self.h, self.w, self.ch = frame.shape
        self.set_perspective_parameters()
        self.isActive = ret
        
        if self.shape == 'ELLIPSE':
            frame = self.correct_frame_perspective(frame)
        return frame

    def get_frame(self) -> np.ndarray:
        ret, frame = self.feed.read()
        self.isActive = ret

        if (self.crop_points is not None) and ret:
            frame = frame[self.crop_points[0][0]:self.crop_points[0][1], 
                          self.crop_points[1][0]:self.crop_points[1][1]]
        
        if self.shape == 'ELLIPSE' and ret:
            frame = self.correct_frame_perspective(frame)

        return frame if ret else np.zeros_like(frame)

    def draw_optical_flow(self, image: np.ndarray, old_points: list, new_points: list, overwrite = False) -> np.ndarray:
        if overwrite:
            self.mask = np.zeros_like(image)
        
        for i, (new, old) in enumerate(zip(new_points, old_points)):
            a, b = new.ravel()
            c, d = old.ravel()
            self.mask = cv.line(self.mask, (int(a), int(b)), (int(c), int(d)), self.color[i].tolist(), 2)
            image = cv.circle(image, (int(a), int(b)), 5, self.color[i].tolist(), -1)

        #Draws the boundaries for the crosshair (feature mask)
        red = [0,0,255]
        fromx, tox, fromy, toy = self.maskpoints
        cv.circle(self.mask, (fromx,toy), 4, red, -1)
        cv.circle(self.mask, (fromx,fromy), 4, red, -1)
        cv.circle(self.mask, (tox,fromy), 4, red, -1)
        cv.circle(self.mask, (tox,toy), 4, red, -1) 

        return (cv.add(self.mask, image))

    def get_optical_flow_vectors(self) -> tuple:
        old_frame_gray = cv.cvtColor(self.old_frame, cv.COLOR_BGR2GRAY)
        new_frame = self.get_frame()
        if not self.isActive:
            return (None, None)

        new_frame_gray = cv.cvtColor(new_frame, cv.COLOR_BGR2GRAY)
        
        # find features in our old grayscale frame. feature mask is dynamic but manual
        p0 = cv.goodFeaturesToTrack(old_frame_gray, mask = self.feature_mask, **self.st_params)
        p1, st, err = cv.calcOpticalFlowPyrLK(old_frame_gray, new_frame_gray, p0, None, **self.lk_params)

        #Select good tracking points based on successful tracking
        if p1 is not None:
            good_new = p1[(st == 1) & (abs(err) < self.threshold)]
            good_old = p0[(st == 1) & (abs(err) < self.threshold)]

        #Set the new frame to be considered "old" for next call
        self.old_frame = new_frame

        return (good_new, good_old), new_frame