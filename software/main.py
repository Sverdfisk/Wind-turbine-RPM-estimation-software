import cv2 as cv
from rpm import opticalflow as flow
from rpm import calculate_rpm as crpm
from rpm import utils
import numpy as np
import argparse
np.set_printoptions(formatter={'all':lambda x: str(x)})

# --------Keep this file short!--------
# Main runner file, only used to setup and run the actual scripts.
# Look at rpm/opticalflow.py and rpm/calculate_rpm.py for details

parser = argparse.ArgumentParser()
parser.add_argument('cfg')
parser.add_argument('-l', '--log', action='store_true', required=False, help="Enables logging of runs")
parser.add_argument('-r', '--runs', type=int, required=False, default=10, help="Override number of runs")
args = parser.parse_args()
params = utils.parse_json(args.cfg)

run_number = 1
for i in range(0, args.runs):
    print(f'STARTING RUN {run_number}')
    rpms = []
    errors = []

    #restart the feed for every run
    feed = flow.opticalflow(params["target"], 
                            crop_points =        params["crop_points"], 
                            crosshair_size =     params["crosshair_size"], 
                            fps =                params["fps"],
                            crosshair_offset_x = params["crosshair_offset_x"],
                            crosshair_offset_y = params["crosshair_offset_y"],
                            ground_angle =       params["ground_angle"])
    
    while feed.isActive:
        data, image = feed.get_optical_flow_vectors()
        if (data is None) or (image is None): # If this happens, the video/gif is complete or the feed is interrupted
            break

        # The data indices have pixel positions, the total movement in one frame is new_pos - old_pos
        motion_vectors = (data[0]-data[1]) 
        scaled_vectors = motion_vectors * feed.rpm_scaling_factor
        rpm = crpm.get_rpm(motion_vectors, params["radius_max"], params["fps"])

        #Ensure that dead frames do not get counted 
        if rpm is not None:
            rpms.append(rpm)
            error = utils.calculate_error_percentage(rpm, params["real_rpm"])
            errors.append(error)

        flow_image = feed.draw_optical_flow(image, data[1], data[0])
        cv.imshow('Image feed', flow_image) # This MUST be called to refresh frames.
        k = cv.waitKey(30) & 0xff
        if k == 27:
            break

    if args.log:
        utils.print_statistics(rpms, errors, real_rpm=params["real_rpm"])
        utils.write_output(params["id"], run_number, rpms, params["real_rpm"])
    run_number += 1

cv.destroyAllWindows()
