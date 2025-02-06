import cv2 as cv
from rpm import opticalflow as flow
import time
import numpy as np

# --------Keep this file short!--------
# Main runner file, only used to setup and run the actual scripts.
# Look at rpm/opticalflow.py and rpm/calculate_rpm.py for details

# Feed configuration
np.set_printoptions(formatter={'all':lambda x: str(x)})
feed_path = '/home/ken/projects/windturbine/software/rpm/windturbine2.gif'
crop_points = [[60,340],[40,320]]
crosshair_size = [30,30]
frame_rate = 10

if ((crop_points[0][1] - crop_points[0][0]) == (crop_points[1][1] - crop_points[1][0])):
    print("SQUARE CHECK OK")

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
        flow_image = feed.draw_optical_flow(image, data[0], data[1])

        print(data[1] - data[0])

        cv.imshow('Camera feed', flow_image)
        k = cv.waitKey(30) & 0xff
        if k == 27:
            break