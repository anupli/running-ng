#!/usr/env/bin python3
import logging
import argparse

from running.__version__ import __VERSION__

logger = logging.getLogger(__name__)


def setup_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="change logging level to DEBUG")               
    parser.add_argument("--version", action="version",
                        version="running {}".format(__VERSION__))
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


if __name__ == "__main__":
    main()
