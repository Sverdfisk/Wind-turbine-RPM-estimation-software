import os
from datetime import datetime
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


def main(feed, params, start_time):
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

                cv.imshow("Image feed", flow_image)
                k = cv.waitKey(30) & 0xFF
                if k == 27:
                    break

            else:
                if args.deploy:
                    utils.write_output(params["id"], 0, rpms, params["real_rpm"])
                break

    elif isinstance(feed, bpm_cascade.BpmCascade):
        frame = feed.get_frame()

        # Region and processing setup
        box_params = feed.get_fitted_box_params_from_cfg()
        bounds = feed.cascade_bounding_boxes(*box_params)
        kernel_er_dil_params = feed.get_dilation_erosion_params()

        # Filtering setup
        # deque for ease of use, we only need the last 2 ticks to measure tick time
        frame_ticks = deque(maxlen=2)
        fb_average_long_buffer = deque(maxlen=int(params["fps"]))
        rpm_buffer = deque(maxlen=params["rpm_buffer_length"])
        tick_time = start_time
        deviation, mode = 0, 0
        prev_rpm, rpm = 0, 0

        while True:
            if feed.isActive:
                # To start, we loop through each bounding box and look at its contents
                # Each box gets its own frame buffer
                for bounding_box in bounds.values():
                    # Process the region within the box
                    processed_region = bounding_box.dilate_and_erode(
                        frame, *kernel_er_dil_params
                    )

                    # Save processed regions/subimages in frame buffer
                    bounding_box.fb.insert(processed_region)

                    #  Draw a  border around the bounding box processed region
                    #  call this after inserting the region into the frame buffer!!!!
                    #  if not we do computations on the region WITH borders drawn on
                    if not args.deploy:
                        bounding_box.draw.border_around_region(
                            processed_region, 1, [0, 255, 0]
                        )
                        # Draw processing
                        frame = bounding_box.draw.processing_results(
                            frame, bounding_box.region, processed_region
                        )

                    bounding_box.fb.update_color_delta_average()

                # Update decection values
                if feed.frame_cnt % feed.color_delta_update_frequency == 0:
                    feed.update_global_fb_average()
                    fb_average_long_buffer.append(feed.all_fb_delta_average)
                    mode = utils.find_top_n_modes(fb_average_long_buffer, 1)

                    # Only useful if there is more than 1 mode
                    mode = np.mean(mode)
                    deviation = np.std(fb_average_long_buffer)

                # Check if the new values indicate a detection
                if feed.blade_detection_in_box_regions(float(deviation), float(mode)):
                    # Note the frame we detect the blade
                    frame_ticks.append(feed.frame_cnt)

                    # We cant do calculations with one detection
                    if len(frame_ticks) == 2:
                        rpm = feed.calculate_rpm(
                            frame_ticks[1] - frame_ticks[0], feed.fps
                        )

                        # Ignore detections if they are unreasonable.
                        # The ticks are stored but the output is not updated
                        if rpm_buffer:
                            last_output = rpm_buffer[-1]

                            # Turbines wont spin faster than 30RPM. they will not "brake"
                            # faster than a loss of 3 RPM per third of a rotation.
                            # Detections saying otherwise are assumed false.
                            if rpm < 30 or (
                                (last_output - 3) < rpm < (last_output + 3)
                            ):
                                rpm_buffer.append(rpm)

                        # The first detection we append anyway
                        else:
                            rpm_buffer.append((rpm if rpm < 30 else 0))

                    # Stop additional triggers until we've stabilized
                    feed.detection_enable_toggle = False

                feed.update_detection_enable_toggle(
                    feed.all_fb_delta_average, deviation, mode
                )

                # Write, print and other final steps
                if args.deploy:
                    if feed.frame_cnt % 1000 == 0:
                        print("RPM calculation is running...")
                    # Only append new values
                    if rpm != prev_rpm:
                        tick_timestamp = datetime.now()
                        output_file.write(
                            utils.dynamic_log_string(
                                feed,
                                tick_timestamp,
                                (
                                    feed.all_fb_delta_average,
                                    mode,
                                    (mode + feed.threshold_multiplier * deviation),
                                ),
                                rpm_buffer,
                            )
                        )
                else:
                    smoothed_rpm = [round(np.mean(rpm_buffer), 3)]
                    feed.print_useful_stats(
                        out=smoothed_rpm,
                        frame_ticks=frame_ticks,
                        detection_enable_toggle=feed.detection_enable_toggle,
                        threshold=(mode + feed.threshold_multiplier * deviation),
                        mode=mode,
                    )

                    cv.imshow("Image feed", frame)
                    k = cv.waitKey(1) & 0xFF
                    if k == 27:
                        break

                # Update the frame and set rpm to prev_rpm
                frame = feed.get_frame()
                prev_rpm = rpm

            else:
                break


if __name__ == "__main__":
    np.set_printoptions(threshold=np.inf)
    parser = argparse.ArgumentParser()
    parser.add_argument("cfg")
    parser.add_argument(
        "-d",
        "--deploy",
        action="store_true",
        required=False,
        help="",
    )
    args = parser.parse_args()
    params = utils.parse_json(args.cfg)

    current_time = datetime.now()
    current_time_string = current_time.strftime("%d/%m/%Y %H:%M:%S")

    # Open this file globally in production mode to avoid excessive open/closes
    if args.deploy:
        os.makedirs(os.path.dirname("runs/out.csv"), exist_ok=True)
        output_file = open("runs/out.csv", "w")
        output_file.write(f"Logging started at {current_time_string}\n")

    # restart the feed for every run
    if params["mode"] == "bpm":
        feed = bpm_cascade.BpmCascade(**params)
    else:
        feed = opticalflow.OpticalFlow(**params)

    main(feed, params, current_time)

    if args.deploy:
        end_time = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        output_file.write(f"Logging ended at {end_time}\n")

    else:
        cv.destroyAllWindows()
