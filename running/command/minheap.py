from running.config import Configuration
from pathlib import Path
from running.runtime import NativeExecutable, Runtime
from running.benchmark import JavaBenchmark
from running.suite import JavaBenchmarkSuite
from running.util import parse_config_str
import logging
import tempfile


def setup_parser(subparsers):
    f = subparsers.add_parser("minheap")
    f.set_defaults(which="minheap")
    f.add_argument("CONFIG", type=Path)


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
        if b"PASSED" in output:
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


def run(args):
    if args.get("which") != "minheap":
        return False
    configuration = Configuration.from_file(args.get("CONFIG"))
    configuration.resolve_class()
    suites = configuration.get("suites")
    maxheap = configuration.get("maxheap")
    with tempfile.TemporaryDirectory(prefix="minheap-") as minheap_dir:
        logging.info("Temporary directory: {}".format(minheap_dir))
        for suite_name, bms in configuration.get("benchmarks").items():
            suite = suites[suite_name]
            for b in bms:
                print("{}-{}".format(b.suite_name, b.name))
                for c in configuration.get("configs"):
                    runtime, mods = parse_config_str(configuration, c)
                    if isinstance(runtime, NativeExecutable):
                        logging.warning(
                            "Minheap measurement not supported for NativeExecutable")
                    mod_b = b.attach_modifiers(mods)
                    minheap = minheap_one_bm(suite, runtime, mod_b, maxheap, minheap_dir)
                    print("minheap {}".format(minheap))
    return True
