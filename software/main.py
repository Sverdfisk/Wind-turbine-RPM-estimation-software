import cv2 as cv
import numpy as np
from collections import deque
from rpm import opticalflow
from rpm import bpm_cascade
from rpm import utils
import argparse

# --------Keep this file short!--------
# Main runner file, only used to setup and run the actual scripts.
# Look at rpm/opticalflow.py and rpm/calculate_rpm.py for details


def main(feed, params):
    # TODO: refactor the entirety of opticalflow.py
    #  Flow method setup
    rpms = []
    errors = []
    if isinstance(feed, opticalflow.OpticalFlow):
        while True:
            if feed.isActive:
                # Gets optical flow vectors (automatically fetches frames)
                data, image = feed.get_optical_flow_vectors()

                #  Avoids a crash when OpenCV gets an empty frame
                if image is None:
                    continue

                # if tracking is successful, data will not have None
                if all(x is not None for x in data):
                    motion_vectors = data[0] - data[1]
                    scaled_vectors = motion_vectors * feed.rpm_scaling_factor
                    rpm = feed.calculate_rpm_from_vectors(scaled_vectors)
                    flow_image = feed.draw_optical_flow(image, data[1], data[0])

                # Set some defaults that we filter out if tracking is unsuccessful
                else:
                    rpm = None
                    flow_image = image

                # Find RPM and error rate
                if rpm is not None:
                    rpms.append(rpm)
                    error = utils.calculate_error_percentage(rpm, params["real_rpm"])
                    errors.append(error)

                # This MUST be called to refresh frames.
                cv.imshow("Image feed", flow_image)
                k = cv.waitKey(30) & 0xFF
                if k == 27:
                    break

            else:
                #  Logging is handled externally if the script is run from multirunner.py
                if __name__ == "__main__":
                    if args.log:
                        utils.write_output(params["id"], 0, rpms, params["real_rpm"])
                else:
                    return rpms, errors
                break

    elif isinstance(feed, bpm_cascade.BpmCascade):
        frame = feed.get_frame()
        box_params = feed.fit_box_parameters_to_radius(
            params["target_num_boxes"],
            params["target_box_size"],
            resize_boxes=params["resize_boxes"],
            adjust_num_boxes=params["adjust_num_boxes"],
        )
        out = []
        bounds = feed.cascade_bounding_boxes(*box_params, params["frame_buffer_size"])
        kernel_er_dil_params = (
            params["erosion_dilation_kernel_size"],
            params["dilation_iterations"],
            params["erosion_iterations"],
        )
        #  deque for ease of use, we only need the last 2 ticks to measure tick time
        frame_ticks = deque(maxlen=2)
        toggle = True

        while True:
            if feed.isActive:
                # To start, we set up the bounding boxes for the algorithm
                # Each box gets its own frame buffer, organized by the box index
                for frame_buffer_index, bounding_box in enumerate(bounds):
                    # Do processing
                    processed_region = bounding_box.detect_blade.dilation_erosion(
                        frame, *kernel_er_dil_params
                    )

                    # Save processed regions/subimages in frame buffer
                    feed.fb.insert(frame_buffer_index, processed_region)

                    # Draw processing
                    frame = bounding_box.draw.processing_results(
                        frame, bounding_box.region, processed_region
                    )

                # Updating the average less frequently reduces susceptibility to noise,
                # but reduces sensitivity to color change. A good value
                # could be between 2-5
                if feed.frame_cnt % params["color_delta_update_frequency"] == 0:
                    feed.fb.update_averages()

                # toggle has reset and we get a big color difference spike
                # note: the spike increases with box size and number of boxes
                if feed.fb.average_delta > 2 and toggle:
                    # Note the frame we detect the blade
                    frame_ticks.append(feed.frame_cnt)

                    # We cant do calculations with one detection
                    if len(frame_ticks) == 2:
                        rpm = bounds[1].detect_blade.calculate_rpm(
                            frame_ticks[1] - frame_ticks[0], params["fps"]
                        )
                        out.append(rpm)

                    # Stop additional triggers until we've stabilized
                    toggle = False

                feed.print_useful_stats(out, frame_ticks, toggle)

                if -1 < feed.fb.average_delta < 1:
                    toggle = True

                # This MUST be called to refresh frames.
                cv.imshow("Image feed", frame)
                k = cv.waitKey(30) & 0xFF
                if k == 27:
                    break

                frame = feed.get_frame()
            else:
                if __name__ == "__main__":
                    avg_rpm = list(set(out))
                    if args.log:
                        utils.write_output(params["id"], 0, avg_rpm, None)
                    return (
                        avg_rpm,
                        None,
                    )  # Fix this!!!! Should return actual error percentage
                break


if __name__ == "__main__":
    np.set_printoptions(threshold=np.inf)
    parser = argparse.ArgumentParser()
    parser.add_argument("cfg")
    parser.add_argument(
        "-l",
        "--log",
        action="store_true",
        required=False,
        help="Enables logging of runs",
    )
    args = parser.parse_args()
    params = utils.parse_json(args.cfg)

    # restart the feed for every run
    if params["mode"] == "bpm":
        feed = bpm_cascade.BpmCascade(**params)
    else:
        feed = opticalflow.OpticalFlow(**params)

    main(feed, params)
    cv.destroyAllWindows()
