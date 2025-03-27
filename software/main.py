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

        # Region and processing setup
        box_params = feed.get_fitted_box_params_from_cfg()
        bounds = feed.cascade_bounding_boxes(
            *box_params, frame_buffer_size=feed.frame_buffer_size
        )
        kernel_er_dil_params = feed.get_dilation_erosion_params()

        # Filtering setup
        # deque for ease of use, we only need the last 2 ticks to measure tick time
        frame_ticks = deque(maxlen=2)
        fb_averages = deque(maxlen=100)
        out = deque(maxlen=5)
        deviation, mode = 0, 0

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

                    #  Draw a  border around the bounding box processed region
                    #  call this after inserting the region into the frame buffer!!!!
                    bounding_box.draw.border_around_region(
                        processed_region, 1, [0, 255, 0]
                    )
                    # Draw processing
                    frame = bounding_box.draw.processing_results(
                        frame, bounding_box.region, processed_region
                    )

                if feed.frame_cnt % feed.color_delta_update_frequency == 0:
                    feed.fb.update_averages()
                    fb_averages.append(feed.fb.average_delta)
                    mode = utils.find_top_n_modes(fb_averages, 1)
                    mode = np.mean(mode)
                    deviation = np.std(fb_averages)

                if feed.intensity_is_over_threshold(float(deviation), float(mode)):
                    # Note the frame we detect the blade
                    frame_ticks.append(feed.frame_cnt)

                    # We cant do calculations with one detection
                    if len(frame_ticks) == 2:
                        rpm = bounds[1].detect_blade.calculate_rpm(
                            frame_ticks[1] - frame_ticks[0], feed.fps
                        )
                        out.append(rpm)

                    # Stop additional triggers until we've stabilized
                    feed.detection_enable_toggle = False

                feed.update_detection_enable_toggle(
                    feed.fb.average_delta, deviation, mode
                )

                #  Print stats
                # feed.print_useful_stats(
                #    out=out,
                #    frame_ticks=frame_ticks,
                #    detection_enable_toggle=feed.detection_enable_toggle,
                #    threshold=float(deviation),
                #    mode=float(mode),
                # )

                smoothed = False

                if smoothed:
                    print(
                        feed.frame_cnt,
                        (0 if out == deque(maxlen=5) else np.mean(np.asarray(out))),
                    )
                else:
                    print(feed.frame_cnt, (0 if out == deque(maxlen=5) else out[-1]))

                # This MUST be called to refresh frames.
                cv.imshow("Image feed", frame)
                k = cv.waitKey(30) & 0xFF
                if k == 27:
                    break
                # Update the frame
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
