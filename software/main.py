import cv2 as cv
from rpm import opticalflow
from rpm import utils
import numpy as np
import argparse

# --------Keep this file short!--------
# Main runner file, only used to setup and run the actual scripts.
# Look at rpm/opticalflow.py and rpm/calculate_rpm.py for details


def main(feed, rpms, errors, params):
    while feed.isActive:
        data, image = feed.get_optical_flow_vectors()
        if (data is None) or (image is None):
            break

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
    cv.destroyAllWindows()
    return rpms, errors


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

    rpms = []
    errors = []
    run_number = 1
    # restart the feed for every run
    feed = opticalflow.RpmFromFeed(**params)
    rpms, errors = main(feed, rpms, errors, params)
    if args.log:
        utils.print_statistics(rpms, errors, real_rpm=params["real_rpm"])
        utils.write_output(params["id"], run_number, rpms, params["real_rpm"])

    cv.destroyAllWindows()
