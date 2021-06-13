from typing import Dict
import yaml
from pathlib import Path
from running.benchmark import Benchmark

def load_benchmarks(config: Dict[str, Dict[str, str]]):
    for (bm_name, bm) in config.items():
        print(repr(Benchmark.from_config(bm_name, bm)))


def setup_parser(subparsers):
    f = subparsers.add_parser("minheap")
    f.set_defaults(which="minheap")
    f.add_argument("CONFIG", type=Path)


def run(args):
    if args.get("which") != "minheap":
        return False
    config_path = args.get("CONFIG")
    assert config_path.exists()
    with config_path.open("r") as fd:
        config = yaml.load(fd)
        import pprint; pprint.pprint(config)
        load_benchmarks(config["benchmarks"])
    return True
