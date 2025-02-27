from main import main
from rpm import utils
from rpm import opticalflow
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("cfg")
parser.add_argument(
    "-l",
    "--log",
    action="store_true",
    required=False,
    help="Enables logging of runs",
)
parser.add_argument(
    "-r",
    "--runs",
    type=int,
    required=True,
    default=10,
    help="Set number of runs",
)
args = parser.parse_args()
params = utils.parse_json(args.cfg)

run_number = 1
for i in range(args.runs):
    rpms = []
    errors = []

    # restart the feed for every run
    feed = opticalflow.OpticalFlow(**params)
    rpms, errors = main(feed, params)
    if args.log:
        utils.print_statistics(rpms, errors, real_rpm=params["real_rpm"])
        utils.write_output(params["id"], run_number, rpms, params["real_rpm"])
    run_number += 1
