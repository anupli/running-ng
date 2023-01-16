from typing import Any, Dict, Optional, DefaultDict
from running.config import Configuration
from pathlib import Path
from running.runtime import NativeExecutable, Runtime
from running.benchmark import Benchmark, SubprocessrExit
from running.suite import BenchmarkSuite
from running.util import parse_config_str, config_str_encode
import logging
import tempfile
import yaml
from running.suite import is_dry_run
from collections import defaultdict
from enum import Enum
import os

configuration: Configuration


def setup_parser(subparsers):
    f = subparsers.add_parser("minheap")
    f.set_defaults(which="minheap")
    f.add_argument("CONFIG", type=Path)
    f.add_argument("RESULT", type=Path)
    f.add_argument("-a", "--attempts", type=int)


class ContinueSearch(Enum):
    Abort = 1
    HeapTooBig = 2
    HeapTooSmall = 3


def run_bm_with_retry(suite: BenchmarkSuite, runtime: Runtime, bm_with_heapsize: Benchmark, minheap_dir: Path, attempts: int) -> ContinueSearch:
    def log(s):
        return print(s, end="", flush=True)

    log(" ")
    for _ in range(attempts):
        output, _companion_output, subprocess_exit = bm_with_heapsize.run(
            runtime, cwd=minheap_dir)
        if runtime.is_oom(output):
            # if OOM is detected, we exit the loop regardless the exit statussour
            log("x ")
            return ContinueSearch.HeapTooSmall
        if subprocess_exit is SubprocessrExit.Normal:
            if suite.is_passed(output):
                log("o ")
                return ContinueSearch.HeapTooBig
        elif subprocess_exit is SubprocessrExit.Timeout:
            # A timeout is likely due to heap being too small and many GCs scheduled back to back
            log("t ")
            return ContinueSearch.HeapTooSmall
        # If not the above scenario, we treat this invocation as a crash or some kind of erroneous state
        log(".")
        continue
    # No successful invocation in the above attempts, but none OOMed either
    # Probably too many crashes, abort the binary search for this benchmark
    log(" ")
    return ContinueSearch.Abort


def minheap_one_bm(suite: BenchmarkSuite, runtime: Runtime, bm: Benchmark, heap: int, minheap_dir: Path, attempts: int) -> float:
    lo = 2
    hi = heap
    mid = (lo + hi) // 2
    minh = float('inf')
    while hi - lo > 1:
        heapsize = runtime.get_heapsize_modifier(mid)
        size_str = "{}M".format(mid)
        print(size_str, end="", flush=True)
        bm_with_heapsize = bm.attach_modifiers([heapsize])
        result = run_bm_with_retry(
            suite, runtime, bm_with_heapsize, minheap_dir, attempts)
        if result is ContinueSearch.Abort:
            return float('inf')
        elif result is ContinueSearch.HeapTooBig:
            minh = mid
            hi = mid
            mid = (lo + hi) // 2
        elif result is ContinueSearch.HeapTooSmall:
            lo = mid
            mid = (lo + hi) // 2
        else:
            raise ValueError("Unhandled ContinueSearch variant")
    return minh


def run_with_persistence(result: Dict[str, Any], minheap_dir: Path, result_file: Optional[Path], attempts: int):
    suites = configuration.get("suites")
    maxheap = configuration.get("maxheap")
    for c in configuration.get("configs"):
        c_encoded = config_str_encode(c)
        if c_encoded not in result:
            result[c_encoded] = {}
        runtime, mods = parse_config_str(configuration, c)
        print("{} ".format(c_encoded))
        if isinstance(runtime, NativeExecutable):
            logging.warning(
                "Minheap measurement not supported for NativeExecutable")
            continue
        for suite_name, bms in configuration.get("benchmarks").items():
            if suite_name not in result[c_encoded]:
                result[c_encoded][suite_name] = {}
            suite = suites[suite_name]
            for b in bms:
                # skip a benchmark if we have measured it
                if b.name in result[c_encoded][suite_name]:
                    continue
                print("\t {}-{} ".format(b.suite_name, b.name), end="")
                mod_b = b.attach_modifiers(mods)
                minheap = minheap_one_bm(
                    suite, runtime, mod_b, maxheap, minheap_dir, attempts)
                print("minheap {}".format(minheap))
                result[c_encoded][suite_name][b.name] = minheap
                if result_file:
                    with result_file.open("w") as fd:
                        yaml.dump(result, fd)


def print_best(result: Dict[str, Dict[str, Dict[str, float]]]):
    minheap: DefaultDict[str, DefaultDict[str, float]]
    minheap = defaultdict(lambda: defaultdict(lambda: float('inf')))
    minheap_config: DefaultDict[str, DefaultDict[str, str]]
    minheap_config = defaultdict(lambda: defaultdict(lambda: "ALL_FAILED"))
    for config, suites in result.items():
        for suite, benchmark_heap_sizes in suites.items():
            for benchmark, heap_size in benchmark_heap_sizes.items():
                if heap_size < minheap[suite][benchmark]:
                    minheap[suite][benchmark] = heap_size
                    minheap_config[suite][benchmark] = config

    config_best_count: DefaultDict[str, int]
    config_best_count = defaultdict(int)
    for suite, benchmark_configs in minheap_config.items():
        for benchmark, best_config in benchmark_configs.items():
            config_best_count[best_config] += 1

    if config_best_count.items():
        config, count = max(config_best_count.items(), key=lambda x: x[1])
        print("{} obtained the most number of smallest minheap sizes: {}".format(
            config, count))
        print("Minheap configuration to be copied to runbms config files")
        print(yaml.dump(result[config]))


def run(args):
    if args.get("which") != "minheap":
        return False
    global configuration
    configuration = Configuration.from_file(
        Path(os.getcwd()), args.get("CONFIG"))
    configuration.resolve_class()
    result_file = args.get("RESULT")
    if result_file.exists():
        with result_file.open() as fd:
            result = yaml.safe_load(fd)
            if result is None:
                result = {}
    else:
        result = {}
    attempts = configuration.get("attempts")
    if args.get("attempts"):
        attempts = args.get("attempts")
    with tempfile.TemporaryDirectory(prefix="minheap-") as minheap_dir:
        logging.info("Temporary directory: {}".format(minheap_dir))
        if is_dry_run():
            run_with_persistence(result, Path(minheap_dir), None, attempts)
        else:
            run_with_persistence(result, Path(
                minheap_dir), result_file, attempts)
    print_best(result)
    return True
