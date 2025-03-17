import cv2 as cv
from collections import deque
from rpm import opticalflow
from rpm import bpm_cascade
from rpm import utils
import argparse

# --------Keep this file short!--------
# Main runner file, only used to setup and run the actual scripts.
# Look at rpm/opticalflow.py and rpm/calculate_rpm.py for details


def main(feed, params):
    rpms = []
    errors = []
    if isinstance(feed, opticalflow.OpticalFlow):
        while True:
            if feed.isActive:
                data, image = feed.get_optical_flow_vectors()

                # Intentional short circuit
                if (
                    data is not None
                    and all(arr.size == 0 for arr in data)
                    or (image is None)
                ):
                    continue

                # The data indices have pixel positions,
                motion_vectors = data[0] - data[1]
                scaled_vectors = motion_vectors * feed.rpm_scaling_factor
                rpm = feed.calculate_rpm_from_vectors(scaled_vectors)

                # Ensure that dead frames do not get counted
                if rpm is not None:
                    rpms.append(rpm)
                    error = utils.calculate_error_percentage(rpm, params["real_rpm"])
                    errors.append(error)
                flow_image = feed.draw_optical_flow(image, data[1], data[0])

                # This MUST be called to refresh frames.
                cv.imshow("Image feed", flow_image)
                k = cv.waitKey(30) & 0xFF
                if k == 27:
                    break

            else:
                # TODO: refactor this
                if __name__ == "__main__":
                    if args.log:
                        utils.write_output(params["id"], 0, rpms, params["real_rpm"])
                break

        return rpms, errors

    elif isinstance(feed, bpm_cascade.BpmCascade):
        frame = feed.get_frame()
        box_params = (3, 2)
        out = []
        bounds = feed.cascade_bounding_boxes(*box_params, queue_length=3)
        frame_ticks = deque(maxlen=2)
        toggle = True

        while True:
            if feed.isActive:
                # Each box gets its own frame buffer, organized by the box index
                for frame_buffer_index, bounding_box in enumerate(bounds):
                    # Do processing
                    processed_region = bounding_box.detect_blade.dilation_erosion(
                        frame, (6, 6), 10, 20
                    )

                    # Save processed regions in frame buffer
                    feed.fb.insert(frame_buffer_index, processed_region)
                    # Draw processing
                    frame = bounding_box.draw.processing_results(
                        frame, bounding_box.region, processed_region
                    )

                if feed.frame_cnt % 2 == 0:
                    feed.fb.update_averages()

                # toggle has reset and we get a blade detection
                if feed.fb.average > 0 and toggle:
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

                print(
                    f"frame: {feed.frame_cnt} - color diff: {
                        feed.fb.average
                    } - detect enabled: {toggle} - latest measured RPM: {
                        0 if out == [] else round(out[-1], 1)
                    } - last detection at: {
                        None if frame_ticks == deque(maxlen=2) else frame_ticks[-1]
                    }"
                )

                if feed.fb.average == 0:
                    toggle = True

                # This MUST be called to refresh frames.
                cv.imshow("Image feed", frame)
                k = cv.waitKey(30) & 0xFF
                if k == 27:
                    break

                frame = feed.get_frame()
            else:
                # utils.log
                break


if __name__ == "__main__":
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
