import cv2 as cv
from rpm import opticalflow as flow
from rpm import calculate_rpm as crpm
from rpm import utils
import numpy as np
import math
import argparse
np.set_printoptions(formatter={'all':lambda x: str(x)})


#parser = argparse.ArgumentParser()

#parser.add_argument('-f', '--fps', type=float, required=True, help="input feed FPS")
#parser.add_argument('-r', '--real_rpm', type=float, required=False, help="real rpm of wind turbine in feed")
#args = parser.parse_args()
# --------Keep this file short!--------
# Main runner file, only used to setup and run the actual scripts.
# Look at rpm/opticalflow.py and rpm/calculate_rpm.py for details

# Feed configuration
feed_path = '/home/ken/projects/windturbine/software/assets/windturbine4_angle_f12.5_r11.gif'
#fps = args.fps
#real_rpm = args.real_rpm

fps = 12.5
real_rpm = 11

# Feed configuration
crop_points = [[0, 195],[335,430]]
crosshair_size = [40,35]
radius_y = (crop_points[0][1] - crop_points[0][0])
radius_x = (crop_points[1][1] - crop_points[1][0])

radius = radius_y if (radius_y > radius_x) else radius_x

run_number = 1
for i in range(0,20):
    print(f'STARTING RUN {run_number}')
    rpms = []
    errors = []
    #restart the feed for every run
    feed = flow.opticalflow(feed_path, 
                        crop_points = crop_points, 
                        crosshair_size = crosshair_size, 
                        fps=fps,
                        crosshair_offset_x=25)
    
    while feed.isActive:
        data, image = feed.get_optical_flow_vectors()
        if (data is None) or (image is None): # If this happens, the video/gif is complete or the feed is interrupted
            break

        # The data indices have pixel positions, the total movement in one frame is new_pos - old_pos
        motion_vectors = data[1]-data[0]
        rpm = crpm.get_rpm(motion_vectors, radius, fps)

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
    #utils.print_statistics(rpms, errors, real_rpm=real_rpm)
    with open("runs/run_results4_perspective_correction.csv", "a") as myfile:
        myfile.write(f"{run_number}, {np.average(rpms)}, {utils.calculate_error_percentage(np.average(rpms), real_rpm)}\n")
    run_number += 1

cv.destroyAllWindows()
