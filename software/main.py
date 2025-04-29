from sys import intern
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

        # Region and processing setup
        box_params = feed.get_fitted_box_params_from_cfg()
        bounds = feed.cascade_bounding_boxes(*box_params)
        kernel_er_dil_params = feed.get_dilation_erosion_params()

        # Filtering setup
        # deque for ease of use, we only need the last 2 ticks to measure tick time
        frame_ticks = deque(maxlen=2)
        all_fb_averages = deque(maxlen=int(params["fps"]))
        out = deque(maxlen=5)
        deviation, mode = 0, 0
        graph_mode = False
        rpm = 0

        while True:
            if feed.isActive:
                # To start, we set up the bounding boxes for the algorithm
                # Each box gets its own frame buffer, organized by the box index
                for bounding_box in bounds.values():
                    # Do processing
                    processed_region = bounding_box.dilate_and_erode(
                        frame, *kernel_er_dil_params
                    )

                    # Save processed regions/subimages in frame buffer
                    bounding_box.fb.insert(processed_region)

                    #  Draw a  border around the bounding box processed region
                    #  call this after inserting the region into the frame buffer!!!!
                    #  if not we do computations on the region WITH borders drawn on
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
                    all_fb_averages.append(feed.all_fb_delta_average)
                    mode = utils.find_top_n_modes(all_fb_averages, 1)
                    # Only useful if there is more than 1 mode
                    mode = np.mean(mode)
                    deviation = np.std(all_fb_averages)

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
                        if out:
                            last_output = out[-1]

                            # Turbines wont spin faster than 30RPM. they will not "brake"
                            # faster than a loss of 5RPM per third of a rotation.
                            # Detections saying otherwise would be wrong.
                            if rpm < 30 or (
                                (last_output - 5) < rpm < (last_output + 5)
                            ):
                                out.append(rpm)
                            else:
                                pass
                        else:
                            out.append((rpm if rpm < 30 else 0))

                    # Stop additional triggers until we've stabilized
                    feed.detection_enable_toggle = False

                feed.update_detection_enable_toggle(
                    feed.all_fb_delta_average, deviation, mode
                )

                # Print stats
                if graph_mode:
                    smoothed = False
                    # TEMPORARY!!!!!!
                    if smoothed:
                        print(
                            feed.frame_cnt,
                            feed.all_fb_delta_average,
                        )
                    else:
                        print(
                            f"{feed.frame_cnt}, {0 if not out else out[-1]}, {utils.calculate_error_percentage((0 if not out else out[-1]), feed.real_rpm)}"
                        )
                else:
                    # TEMPORARY!!!!!!
                    feed.print_useful_stats(
                        out=out,
                        frame_ticks=frame_ticks,
                        detection_enable_toggle=feed.detection_enable_toggle,
                        threshold=float((mode + feed.threshold_multiplier * deviation)),
                        mode=float(mode),
                        intensity_accel=float(0),
                    )

                cv.imshow("Image feed", frame)
                k = cv.waitKey(1) & 0xFF
                if k == 27:
                    break
                if args.log:
                    utils.write_output(1, feed.frame_cnt, rpm, feed.real_rpm)
                # Update the frame
                frame = feed.get_frame()
            else:
                if __name__ == "__main__":
                    rpms = list(set(out))
                    return (
                        rpms,
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
