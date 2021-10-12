from typing import Any, BinaryIO, Dict, Optional
from running.config import Configuration
from pathlib import Path
from running.runtime import NativeExecutable, Runtime
from running.benchmark import JavaBenchmark
from running.suite import JavaBenchmarkSuite
from running.util import parse_config_str, config_str_encode
import logging
import tempfile
import yaml
from running.suite import is_dry_run

configuration: Configuration

def setup_parser(subparsers):
    f = subparsers.add_parser("minheap")
    f.set_defaults(which="minheap")
    f.add_argument("CONFIG", type=Path)
    f.add_argument("RESULT", type=Path)


def minheap_one_bm(suite: JavaBenchmarkSuite, runtime: Runtime, bm: JavaBenchmark, heap: int, minheap_dir: Path) -> float:
    lo = 2
    hi = heap
    mid = (lo + hi) // 2
    minh = float('inf')
    print("\t{} ".format(runtime.name), end="")
    timeout = suite.get_timeout(bm.name)
    while hi - lo > 1:
        heapsize = runtime.get_heapsize_modifier(mid)
        size_str = "{}M".format(mid)
        print(size_str, end="", flush=True)
        bm_with_heapsize = bm.attach_modifiers([heapsize])
        output, _ = bm_with_heapsize.run(runtime, timeout=timeout, cwd=minheap_dir)
        if suite.is_passed(output):
            print(" o ", end="", flush=True)
            minh = mid
            hi = mid
            mid = (lo + hi) // 2
        else:
            if suite.is_oom(output):
                print(" x ", end="", flush=True)
            else:
                print(" ? ", end="", flush=True)
            lo = mid
            mid = (lo + hi) // 2
    return minh


def run_with_persistence(result: Dict[str, Any], minheap_dir: Path, fd: Optional[BinaryIO]):
    suites = configuration.get("suites")
    maxheap = configuration.get("maxheap")
    for suite_name, bms in configuration.get("benchmarks").items():
        if suite_name not in result:
            result[suite_name] = {}
        suite = suites[suite_name]
        for b in bms:
            if b.name not in result[suite_name]:
                result[suite_name][b.name] = {}
            print("{}-{}".format(b.suite_name, b.name))
            for c in configuration.get("configs"):
                # skip a configuration if we have measured it
                c_encoded = config_str_encode(c)
                if c_encoded in result[suite_name][b.name]:
                    continue
                runtime, mods = parse_config_str(configuration, c)
                if isinstance(runtime, NativeExecutable):
                    logging.warning(
                        "Minheap measurement not supported for NativeExecutable")
                    pass
                mod_b = b.attach_modifiers(mods)
                minheap = minheap_one_bm(suite, runtime, mod_b, maxheap, minheap_dir)
                print("minheap {}".format(minheap))
                result[suite_name][b.name][c_encoded] = minheap
                if fd:
                    yaml.dump(result, fd)

def run(args):
    if args.get("which") != "minheap":
        return False
    global configuration
    configuration = Configuration.from_file(args.get("CONFIG"))
    configuration.resolve_class()
    result_file = args.get("RESULT")
    if result_file.exists():
        with result_file.open() as fd:
            result = yaml.safe_load(fd)
            if result is None:
                result = {}
    else:
        result = {}
    with tempfile.TemporaryDirectory(prefix="minheap-") as minheap_dir:
        logging.info("Temporary directory: {}".format(minheap_dir))
        if is_dry_run():
            run_with_persistence(result, minheap_dir, None)
        else:
            with result_file.open("w") as fd:
                run_with_persistence(result, minheap_dir, fd)

    return True
