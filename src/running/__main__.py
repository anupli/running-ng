#!/usr/env/bin python3
import logging
import argparse

from running.__version__ import __VERSION__
from running.command import fillin, runbms, minheap, log_preprocessor
from running.suite import set_dry_run
import importlib.resources
import os

logger = logging.getLogger(__name__)

MODULES = [fillin, runbms, minheap, log_preprocessor]


def setup_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="change logging level to DEBUG")
    parser.add_argument("--version", action="version",
                        version="running {}".format(__VERSION__))
    parser.add_argument("-d", "--dry-run", action="store_true",
                        help="dry run")
    subparsers = parser.add_subparsers()
    for m in MODULES:
        m.setup_parser(subparsers)
    return parser


def main():
    parsers = setup_parser()
    args = vars(parsers.parse_args())

    # Config root logger
    if args.get("verbose") == True:
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO
    logging.basicConfig(
        format="[%(levelname)s] %(asctime)s %(filename)s:%(lineno)d %(message)s",
        level=log_level)

    if args.get("dry_run") == True:
        set_dry_run(True)
    with importlib.resources.path(__package__, "config") as config_path:
        os.environ["RUNNING_NG_PACKAGE_DATA"] = str(config_path)
        for m in MODULES:
            if m.run(args):
                break
        else:
            parsers.print_help()


if __name__ == "__main__":
    main()
