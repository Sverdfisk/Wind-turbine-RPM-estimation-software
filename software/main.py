import cv2 as cv
from rpm import opticalflow
from rpm import bpm_cascade
from rpm import utils
import numpy as np
import argparse

# --------Keep this file short!--------
# Main runner file, only used to setup and run the actual scripts.
# Look at rpm/opticalflow.py and rpm/calculate_rpm.py for details


def main(feed, mode, params):
    rpms = []
    errors = []
    if mode == "optical flow":
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
                        utils.write_output(
                            params["id"], 0, np.mean(rpms), params["real_rpm"]
                        )
                break

        cv.destroyAllWindows()
        return rpms, errors

    elif mode == "bpm":
        _ = feed.get_frame()
        box_params = (6, 10)
        bounds = feed.cascade_bounding_boxes(*box_params, queue_length=15)
        while True:
            frame = feed.get_frame()

            if feed.isActive:
                # Each box gets its own frame buffer, organized by the box index
                for frame_buffer_index, bounding_box in enumerate(bounds):
                    # Do processing
                    processed_region = bounding_box.detect_blade.dilation_erosion(
                        frame, (15, 15), 10, 20
                    )

                    # Save processed regions in frame buffer
                    feed.fb.insert(frame_buffer_index, processed_region)
                    # Draw processing
                    frame = bounding_box.draw.processing_results(
                        frame, bounding_box.region, processed_region
                    )

                # This MUST be called to refresh frames.
                cv.imshow("Image feed", frame)
                k = cv.waitKey(30) & 0xFF
                if k == 27:
                    break
            else:
                # utils.log
                break


if __name__ == "__main__":
    np.set_printoptions(formatter={"all": lambda x: str(x)})
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
    mode = "bpm"
    # restart the feed for every run
    # feed = opticalflow.OpticalFlow(**params)
    feed = bpm_cascade.BpmCascade(**params)
    rpms, errors = main(feed, mode, params)

    cv.destroyAllWindows()
