import numpy as np
import cv2 as cv


class videoflow():
    def __init__(self,
                 video_feed,
                 st_params, 
                 lk_params, 
                 crop_points = None
                 ):
        self.video_feed = video_feed
        self.shi_tomasi_params = self.set_shi_tomasi_params(st_params)
        self.lucas_kanade_params = self.set_lucas_kanade_params(lk_params)
        self.crop_points = crop_points

    def set_shi_tomasi_params(maxCorners = 100, 
                            qualityLevel = 0.3, 
                            minDistance = 7, 
                            blockSize = 7):
        return locals()

    def set_lucas_kanade_params(winSize = (15, 15), 
                                maxLevel = 2, 
                                criteria = (cv.TERM_CRITERIA_EPS | cv.TERM_CRITERIA_COUNT, 10, 0.03)):
        return locals()

    def draw_flow_from_points(self, mask, old_frame, frame, points_0, points_1, status, 
                        colors = np.random.randint(0, 255, (100, 3))
                        ):

        # Select good points
        if points_1 is not None:
            good_new = points_1[status==1]
            good_old = points_0[status==1]

        # draw the tracks
        for i, (new, old) in enumerate(zip(good_new, good_old)):
            a, b = new.ravel()
            c, d = old.ravel()
            mask = cv.line(mask, (int(a), int(b)), (int(c), int(d)), colors[i].tolist(), 2)
            frame = cv.circle(frame, (int(a), int(b)), 5, colors[i].tolist(), -1)

        return frame, mask, good_new

    def get_optical_flow(self,
                         video_feed,
                         st_params, 
                         lk_params, 
                         crop_points = None
                            ):
        # read a frame
        ret, old_frame = video_feed.read()

        if crop_points is not None:
            old_frame = old_frame[crop_points[0][0]:crop_points[0][1], 
                                crop_points[1][0]:crop_points[1][1]]

        # Convert to grayscale for algorithmic purposes
        old_gray = cv.cvtColor(old_frame, cv.COLOR_BGR2GRAY)

        while(1):
            #This is the updating frame, we need at least 2 frames to start the algorithm
            ret, frame = video_feed.read()

            if crop_points is not None:
                frame = frame[crop_points[0][0]:crop_points[0][1], 
                            crop_points[1][0]:crop_points[1][1]]
                
            if not ret:
                print('No frames grabbed!')
                break

            # find features in our old grayscale frame
            p0 = cv.goodFeaturesToTrack(old_gray, mask = None, **st_params)
            frame_gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
            # calculate optical flow
            p1, st, err = cv.calcOpticalFlowPyrLK(old_gray, frame_gray, p0, None, **lk_params)
    

            #Reassign to itself as we want to overwrite the old frame with new drawings on top
            frame, mask, good_new = self.draw_flow_from_points(self, mask, old_frame, frame, p0, p1, st)
            # Add the mask over the frame, creating a new image
            img = cv.add(frame, mask)

            # Show/write frame
            cv.imshow('Camera feed', img)
            k = cv.waitKey(30) & 0xff
            if k == 27:
                break

            # Update the previous frame and previous points
            old_gray = frame_gray.copy()
            p0 = good_new.reshape(-1, 1, 2)
            
        cv.destroyAllWindows()
 

if __name__ == '__main__':
    # Set this and pass as an argument in calculate_optical_flow() if other drawing colors are desired
    # colors=np.random.randint(0, 255, (100, 3))
    video_feed_path = '/dev/video2'
    feed = cv.VideoCapture(video_feed_path) 
    # fromx = 140
    # tox = 380
    # fromy = 170
    # toy = 470
    # coords = [[fromx,tox], [fromy,toy]]
    lkparams = get_lucas_kanade_params()
    stparams = get_shi_tomasi_params()

    get_optical_flow(feed, stparams, lkparams)


if __name__ == '__main__':
    # Set this and pass as an argument in calculate_optical_flow() if other drawing colors are desired
    # colors=np.random.randint(0, 255, (100, 3))
    video_feed_path = '/dev/video2'
    feed = cv.VideoCapture(video_feed_path) 
    # fromx = 140
    # tox = 380
    # fromy = 170
    # toy = 470
    # coords = [[fromx,tox], [fromy,toy]]
    lkparams = get_lucas_kanade_params()
    stparams = get_shi_tomasi_params()

    get_optical_flow(feed, stparams, lkparams)