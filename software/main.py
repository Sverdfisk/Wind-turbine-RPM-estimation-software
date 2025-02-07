import cv2 as cv
from rpm import opticalflow as flow
from rpm import calculate_rpm as crpm
from rpm import utils
import time
import numpy as np
np.set_printoptions(formatter={'all':lambda x: str(x)})


# --------Keep this file short!--------
# Main runner file, only used to setup and run the actual scripts.
# Look at rpm/opticalflow.py and rpm/calculate_rpm.py for details

# Feed configuration
feed_path = '/home/ken/projects/windturbine/software/rpm/assets/windturbine.gif'
crop_points = [[70,340],[40,310]]
crosshair_size = [25,25]
frame_rate = 10
real_rpm = 13
radius = (crop_points[0][1] - crop_points[0][0]) / 2
feed = flow.opticalflow(feed_path, 
                        crop_points = crop_points, 
                        crosshair_size = crosshair_size, 
                        fps=frame_rate)

rpms = []
errors = []
prev = 0

while feed.isActive:

    time_elapsed = time.time() - prev
    if time_elapsed > 1./frame_rate:
        prev = time.time()

        data, image = feed.get_optical_flow_vectors()
        if (data is None) or (image is None): # If this happens, the video/gif is complete or the feed is interrupted
            break

        # The data indices have pixel positions, the total movement in one frame is new_pos - old_pos
        motion_vectors = data[1]-data[0]
        rpm = crpm.get_rpm(motion_vectors, radius, frame_rate)

        #Ensure that dead frames do not get counted 
        if rpm is not None:
            rpms.append(rpm)
            error = utils.calculate_error_percentage(rpm, real_rpm)
            errors.append(error)

        flow_image = feed.draw_optical_flow(image, data[1], data[0])
        cv.imshow('Image feed', flow_image)
        k = cv.waitKey(30) & 0xff
        if k == 27:
            break

utils.print_statistics(rpms, errors, real_rpm=real_rpm)
cv.destroyAllWindows()
