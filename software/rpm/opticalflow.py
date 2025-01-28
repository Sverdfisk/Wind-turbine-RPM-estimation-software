import numpy as np
import cv2 as cv

class opticalflow():
    def __init__(self, video_feed_path):
        self.feed = cv.VideoCapture(video_feed_path)
        self.st_params = self.set_shi_tomasi_params()
        self.lk_params = self.set_lucas_kanade_params()
        self.crop_points = self.set_crop_points()
        self.set_crosshair_size()

    def set_crosshair_size(self, size = [10,10]):
        if size is not None:
            self.crosshair_size_x, self.crosshair_size_y = size
        else:
            pass

    def set_crop_points(self, points = None):
        self.crop_points = points

    def set_shi_tomasi_params(self, maxCorners = 100, 
                              qualityLevel = 0.1, 
                              minDistance = 9, 
                              blockSize = 3):
        
        params = dict(maxCorners = maxCorners, 
                      qualityLevel = qualityLevel, 
                      minDistance = minDistance, 
                      blockSize = blockSize)
        return params

    def set_lucas_kanade_params(self, winSize = (15, 15), 
                                maxLevel = 2, 
                                criteria = (cv.TERM_CRITERIA_EPS | cv.TERM_CRITERIA_COUNT, 10, 0.03)):

        params = dict(winSize = winSize, 
                      maxLevel = maxLevel, 
                      criteria = criteria)
        return params

    def translate_coords_to_centre(self, image_height, image_width, sizex = 0, sizey = 0):
        centre = [image_height/2, image_width/2]
        x_left = int(centre[1]-sizex)
        x_right = int(centre[1]+sizex)
        y_top = int(centre[0]-sizey)
        y_bottom = int(centre[0]+sizey)
        return [x_left, x_right, y_top, y_bottom]

    def generate_feature_mask_matrix(self, image):
        size = [self.crosshair_size_x, self.crosshair_size_y]
        height, width, channels = image.shape
        mask = np.full((height, width), 255, dtype=np.uint8)
        x_left, x_right, y_top, y_bottom = self.translate_coords_to_centre(height, width, sizex = size[0], sizey = size[1])
        self.maskpoints = [x_left, x_right, y_top, y_bottom]
        mask[y_top:y_bottom, x_left:x_right] = 0
        return mask

    def get_frame(self):
        ret, frame = self.feed.read()

        if self.crop_points is not None:
            frame = frame[self.crop_points[0][0]:self.crop_points[0][1], 
                      self.crop_points[1][0]:self.crop_points[1][1]]
            
        return frame if ret else np.zeros_like(frame)
    
    # The model uses the mask parameter to ignore the middle.
    # The model is assumes a dead zone is desired with the 
    # wind turbine hub in the centre of the frame.

    def get_optical_flow_vectors(self, frame):

        # We do this to have 2 running frames to calculate flow
        # TODO: see if this can cause unexpected behavior when
        # polled in weird ways from the outside

        old_frame = frame
        old_gray = cv.cvtColor(old_frame, cv.COLOR_BGR2GRAY)

        new_frame = self.get_frame()

        # It does not matter which frame we pass in, just that the
        # image matrix has the correct size
        feature_mask = self.generate_feature_mask_matrix(new_frame)

        # find features in our old grayscale frame. feature mask is dynamic but manual
        p0 = cv.goodFeaturesToTrack(old_gray, mask = feature_mask, **self.st_params)
        frame_gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)

        # calculate optical flow
        p1, st, err = cv.calcOpticalFlowPyrLK(old_gray, frame_gray, p0, None, **self.lk_params)

        #Select good tracking points
        #TODO: implement threshold in indexing here
        if p1 is not None:
            good_new = p1[st==1]
            good_old = p0[st==1]

        return good_old, good_new

