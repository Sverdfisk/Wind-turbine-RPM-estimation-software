import numpy as np
import cv2 as cv

class opticalflow():
    def __init__(self, video_feed_path, crop_points):
        self.feed = cv.VideoCapture(video_feed_path)
        self.old_frame = self.get_frame()
        self.st_params = self.set_shi_tomasi_params()
        self.lk_params = self.set_lucas_kanade_params()
        self.crop_points = self.set_crop_points(crop_points)
        self.set_crosshair_size()
        #Sets initial frame. Is also used as prev_frame when recording starts
        self.color = np.random.randint(0, 255, (100, 3))
        self.feature_mask = self.generate_feature_mask_matrix(self.old_frame)

    def set_crosshair_size(self, size = [10,10]):
        if size is not None:
            self.crosshair_size_x, self.crosshair_size_y = size
        else:
            pass

    def set_mask_size(self, crop_points):
        if self.crop_points is not None:
            self.mask = np.zeros_like(self.old_frame[self.crop_points[0][0]:self.crop_points[0][1], 
                                                     self.crop_points[1][0]:self.crop_points[1][1]])    
        else:
            self.mask = np.zeros_like(self.old_frame)

    def set_crop_points(self, points = None):
        self.crop_points = points
        self.set_mask_size(self.crop_points)

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

    def draw_optical_flow(self, mask, image, old_points, new_points, overwrite = True):
        if overwrite:
            mask = np.zeros_like(image)
        
        for i, (new, old) in enumerate(zip(new_points, old_points)):
            a, b = new.ravel()
            c, d = old.ravel()
            mask = cv.line(mask, (int(a), int(b)), (int(c), int(d)), self.color[i].tolist(), 2)
            image = cv.circle(image, (int(a), int(b)), 5, self.color[i].tolist(), -1)

        return mask, (cv.add(self.mask, image))

    def get_optical_flow_vectors(self):

        old_frame_gray = cv.cvtColor(self.old_frame, cv.COLOR_BGR2GRAY)
        new_frame = self.get_frame()

        # find features in our old grayscale frame. feature mask is dynamic but manual
        p0 = cv.goodFeaturesToTrack(old_frame_gray, mask = self.feature_mask, **self.st_params)

        new_frame_gray = cv.cvtColor(new_frame, cv.COLOR_BGR2GRAY)

        # calculate optical flow
        p1, st, _ = cv.calcOpticalFlowPyrLK(old_frame_gray, new_frame_gray, p0, None, **self.lk_params)

        #Select good tracking points
        #TODO: implement threshold in indexing here
        if p1 is not None:
            good_new = p1[st==1]
            good_old = p0[st==1]

        #Set the new frame to be considered "old" for next call
        self.old_frame = new_frame

        return (good_old, good_new), new_frame

