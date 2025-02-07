import cv2 as cv
from rpm import opticalflow as flow
from rpm import calculate_rpm as crpm
import time
import numpy as np
np.set_printoptions(formatter={'all':lambda x: str(x)})
# --------Keep this file short!--------
# Main runner file, only used to setup and run the actual scripts.
# Look at rpm/opticalflow.py and rpm/calculate_rpm.py for details

# Feed configuration
feed_path = '/home/ken/projects/windturbine/software/rpm/assets/windturbine2.gif'
crop_points = [[0,200],[0,200]]
crosshair_size = [25,25]
frame_rate = 10
radius = (crop_points[0][1] - crop_points[0][0]) / 2


feed = flow.opticalflow(feed_path, 
                        crop_points = crop_points, 
                        crosshair_size = crosshair_size, 
                        fps=frame_rate)


prev = 0
while(1):

    time_elapsed = time.time() - prev
    if time_elapsed > 1./frame_rate:
        prev = time.time()

        # Do image stuff
        # crop_points = AI.do_something_that_fixes_my_problem(model=theGoodOne)
        data, image = feed.get_optical_flow_vectors()
        flow_image = feed.draw_optical_flow(image, data[1], data[0])

        # The data indices have pixel positions, the total movement in one frame is new_pos - old_pos
        motion_vector = data[1]-data[0]

        out = crpm.get_rpm(motion_vector, radius, frame_rate, real_rpm=12)
        print(out)
        cv.imshow('Camera feed', flow_image)
        k = cv.waitKey(30) & 0xff
        if k == 27:
            break