import logging
from typing import DefaultDict, Dict, List, Any, Optional, Set, Tuple, BinaryIO, TYPE_CHECKING
from running.suite import BenchmarkSuite, is_dry_run
from running.benchmark import Benchmark, SubprocessrExit
from running.config import Configuration
from pathlib import Path
from running.util import parse_config_str, system, get_logged_in_users, config_index_to_chr, config_str_encode
import socket
from datetime import datetime
from running.runtime import Runtime
import tempfile
import subprocess
import os
from running.command.fillin import fillin
import math
import yaml
if TYPE_CHECKING:
    from running.plugin.runbms import RunbmsPlugin
from running.__version__ import __VERSION__

configuration: Configuration
minheap_multiplier: float
remote_host: Optional[str]
skip_oom: Optional[int]
skip_timeout: Optional[int]
plugins: Dict[str, Any]
resume: Optional[str]


def setup_parser(subparsers):
    f = subparsers.add_parser("runbms")
    f.set_defaults(which="runbms")
    f.add_argument("LOG_DIR", type=Path)
    f.add_argument("CONFIG", type=Path)
    f.add_argument("N", type=int, nargs='?')
    f.add_argument("n", type=int, nargs='*')
    f.add_argument("-i", "--invocations", type=int)
    f.add_argument("-s", "--slice", type=str)
    f.add_argument("-p", "--id-prefix")
    f.add_argument("-m", "--minheap-multiplier", type=float)
    f.add_argument("--skip-oom", type=int)
    f.add_argument("--skip-timeout", type=int)
    f.add_argument("--resume", type=str)
    f.add_argument("--workdir", type=Path)


def getid() -> str:
    host = socket.gethostname()
    now = datetime.now()
    timestamp = now.strftime("%Y-%m-%d-%a-%H%M%S")
    return "{}-{}".format(host, timestamp)


def spread(spread_factor: int, N: int, n: int) -> float:
    """Spread the numbers

    For example, when we have N = 8, n = 0, 1, ..., 7, N,
    we can have fractions of form n / N with equal distances between them:
    0/8, 1/8, 2/8, ..., 7/8, 8/8

    Sometimes it's desirable to transform such sequence with finer steppings
    at the start than at the end.
    The idea is that when the values are small, even small changes can greatly
    affect the behaviour of a system (such as the heap sizes of GC), so we want
    to explore smaller values at a finer granularity.

    For each n, we define
    n' = n + spread_factor / (N - 1) * (1 + 2 + ... + n-2 + n-1)
    For a consecutive pair (n-1, n), we can see that they are additionally
    (n-1) / (N-1) * spread_factor apart.
    For a special case when n = N, we have N' = N + N/2 * spread_factor,
    and (N'-1, N') is spread_factor apart.

    Let's concretely use spread_factor = 1 as as example.
    Let N and n be the same.
    So we have spread_factor / (N - 1) = 1/7
    n = 0, n' = 0,
    n = 1, n' = 1.
    n = 2, n' = 2 + 1/7
    n = 3, n' = 3 + 1/7 + 2/7 = 3 + 3/7
    ...
    n = 7, n' = 7 + 1/7 + 2/7 + ... + 6/7 = 7 + 21/7 = 10
    n = 8, n' = 8 + 1/7 + 2/7 + ... + 7/7 = 8 + 28/7 = 12

    Parameters
    ----------
    N : int
        Denominator
    spread_factor : int
        How much coarser is the spacing at the end relative to start
        spread_factor = 0 doesn't change the sequence at all
    n: int
        Nominator
    """
    sum_1_n_minus_1 = (n*n - n) / 2
    return n + spread_factor / (N - 1) * sum_1_n_minus_1


def hfac_str(hfac: float) -> str:
    return str(int(hfac*1000))


def get_heapsize(hfac: float, minheap: int) -> int:
    return round(minheap * hfac * minheap_multiplier)


def get_hfacs(heap_range: int, spread_factor: int, N: int, ns: List[int]) -> List[float]:
    start = 1.0
    end = float(heap_range)
    divisor = spread(spread_factor, N, N)/(end-start)
    return [spread(spread_factor, N, n)/divisor + start for n in ns]


def run_benchmark_with_config(c: str, b: Benchmark, runbms_dir: Path, size: Optional[int], fd: Optional[BinaryIO]) -> Tuple[bytes, SubprocessrExit]:
    runtime, mods = parse_config_str(configuration, c)
    mod_b = b.attach_modifiers(mods)
    if size is not None:
        mod_b = mod_b.attach_modifiers([runtime.get_heapsize_modifier(size)])
    if fd:
        prologue = get_log_prologue(runtime, mod_b)
        fd.write(prologue.encode("ascii"))
    output, companion_out, exit_status = mod_b.run(runtime, cwd=runbms_dir)
    if fd:
        fd.write(output)
        if companion_out:
            fd.write(b"*****\n")
            fd.write(companion_out)
    if fd:
        epilogue = get_log_epilogue(runtime, mod_b)
        fd.write(epilogue.encode("ascii"))
    return output, exit_status


def get_filename_no_ext(bm: Benchmark, hfac: Optional[float], size: Optional[int], config: str) -> str:
    return "{}.{}.{}.{}.{}".format(
        bm.name,
        # plotty uses "^(\w+)\.(\d+)\.(\d+)\.([a-zA-Z0-9_\-\.\:\,]+)\.log\.gz$"
        # to match filenames
        hfac_str(hfac) if hfac is not None else "0",
        size if size is not None else "0",
        config_str_encode(config),
        bm.suite_name,
    )


def get_filename(bm: Benchmark, hfac: Optional[float], size: Optional[int], config: str) -> str:
    return get_filename_no_ext(bm, hfac, size, config) + ".log"


def get_filename_completed(bm: Benchmark, hfac: Optional[float], size: Optional[int], config: str) -> str:
    return "{}.gz".format(get_filename(bm, hfac, size, config))


def get_log_epilogue(runtime: Runtime, bm: Benchmark) -> str:
    return ""


def hz_to_ghz(hzstr: str) -> str:
    return "{:.2f} GHz".format(int(hzstr) / 1000 / 1000)


def get_log_prologue(runtime: Runtime, bm: Benchmark) -> str:
    output = "\n-----\n"
    output += "mkdir -p PLOTTY_WORKAROUND; timedrun; "
    output += bm.to_string(runtime)
    output += "\n"
    output += "running-ng v{}\n".format(__VERSION__)
    output += system("date") + "\n"
    output += system("w") + "\n"
    output += system("vmstat 1 2") + "\n"
    output += system("top -bcn 1 -w512 |head -n 12") + "\n"
    output += "Environment variables: \n"
    for k, v in sorted(os.environ.items()):
        output += "\t{}={}\n".format(k, v)
    output += "OS: "
    output += system("uname -a")
    output += "CPU: "
    output += system("cat /proc/cpuinfo | grep 'model name' | head -1")
    output += "number of cores: "
    cores = system("cat /proc/cpuinfo | grep MHz | wc -l")
    output += cores
    has_cpufreq = Path("/sys/devices/system/cpu/cpu0/cpufreq").is_dir()
    if has_cpufreq:
        for i in range(0, int(cores)):
            output += "Frequency of cpu {}: ".format(i)
            output += hz_to_ghz(
                system("cat /sys/devices/system/cpu/cpu{}/cpufreq/scaling_cur_freq".format(i)))
            output += "\n"
            output += "Governor of cpu {}: ".format(i)
            output += system("cat /sys/devices/system/cpu/cpu{}/cpufreq/scaling_governor".format(i))
            output += "Scaling_min_freq of cpu {}: ".format(i)
            output += hz_to_ghz(
                system("cat /sys/devices/system/cpu/cpu{}/cpufreq/scaling_min_freq".format(i)))
            output += "\n"
    return output


def run_one_benchmark(
    invocations: int,
    suite: BenchmarkSuite,
    bm: Benchmark,
    hfac: Optional[float],
    configs: List[str],
    runbms_dir: Path,
    log_dir: Path
):
    p: "RunbmsPlugin"
    bm_name = bm.name
    print(bm_name, end=" ")
    size: Optional[int]  # heap size measured in MB
    if hfac is not None:
        print(hfac_str(hfac), end=" ")
        size = get_heapsize(hfac, suite.get_minheap(bm))
        print(size, end=" ")
    else:
        size = None
    for p in plugins.values():
        p.start_benchmark(hfac, size, bm)
    oomed_count: DefaultDict[str, int]
    oomed_count = DefaultDict(int)
    timeout_count: DefaultDict[str, int]
    timeout_count = DefaultDict(int)
    logged_in_users: Set[str]
    logged_in_users = get_logged_in_users()
    if len(logged_in_users) > 1:
        logging.warning("More than one user logged in: {}".format(
            " ".join(logged_in_users)))
    ever_ran = [False] * len(configs)
    for i in range(0, invocations):
        for p in plugins.values():
            p.start_invocation(hfac, size, bm, i)
        print(i, end="", flush=True)
        for j, c in enumerate(configs):
            config_passed = False
            for p in plugins.values():
                p.start_config(hfac, size, bm, i, c, j)
            if skip_oom is not None and oomed_count[c] >= skip_oom:
                print(".", end="", flush=True)
                continue
            if skip_timeout is not None and timeout_count[c] >= skip_timeout:
                print(".", end="", flush=True)
                continue
            if resume:
                log_filename_completed = get_filename_completed(
                    bm, hfac, size, c)
                if (log_dir / log_filename_completed).exists():
                    print(config_index_to_chr(j), end="", flush=True)
                    continue
            log_filename = get_filename(bm, hfac, size, c)
            logging.debug("Running with log filename {}".format(log_filename))
            runtime, _ = parse_config_str(configuration, c)
            if is_dry_run():
                output, exit_status = run_benchmark_with_config(
                    c, bm, runbms_dir, size, None
                )
                assert exit_status is SubprocessrExit.Dryrun
            else:
                fd: BinaryIO
                with (log_dir / log_filename).open("ab") as fd:
                    output, exit_status = run_benchmark_with_config(
                        c, bm, runbms_dir, size, fd
                    )
                ever_ran[j] = True
            if runtime.is_oom(output):
                oomed_count[c] += 1
            if exit_status is SubprocessrExit.Timeout:
                timeout_count[c] += 1
                print(".", end="", flush=True)
            elif exit_status is SubprocessrExit.Error:
                print(".", end="", flush=True)
            elif exit_status is SubprocessrExit.Normal:
                if suite.is_passed(output):
                    config_passed = True
                    print(config_index_to_chr(j), end="", flush=True)
                else:
                    print(".", end="", flush=True)
            elif exit_status is SubprocessrExit.Dryrun:
                print(".", end="", flush=True)
            else:
                raise ValueError("Not a valid SubprocessrExit value")
            for p in plugins.values():
                p.end_config(hfac, size, bm, i, c, j, config_passed)

        for p in plugins.values():
            p.end_invocation(hfac, size, bm, i)
    for p in plugins.values():
        p.end_benchmark(hfac, size, bm)
    for j, c in enumerate(configs):
        log_filename = get_filename(bm, hfac, size, c)
        if not is_dry_run() and ever_ran[j]:
            subprocess.check_call([
                "gzip",
                log_dir / log_filename
            ])
    print()


def run_one_hfac(
    invocations: int,
    hfac: Optional[float],
    suites: Dict[str, BenchmarkSuite],
    benchmarks: Dict[str, List[Benchmark]],
    configs: List[str],
    runbms_dir: Path,
    log_dir: Path
):
    p: "RunbmsPlugin"
    for p in plugins.values():
        p.start_hfac(hfac)
    for suite_name, bms in benchmarks.items():
        suite = suites[suite_name]
        for bm in bms:
            run_one_benchmark(invocations, suite, bm, hfac,
                              configs, runbms_dir, log_dir)
            rsync(log_dir)
    for p in plugins.values():
        p.end_hfac(hfac)


def ensure_remote_dir(log_dir):
    if not is_dry_run() and remote_host is not None:
        log_dir = log_dir.resolve()
        system("ssh {} mkdir -p {}".format(remote_host, log_dir))


def rsync(log_dir):
    if not is_dry_run() and remote_host is not None:
        log_dir = log_dir.resolve()
        system("rsync -ae ssh {}/ {}:{}".format(log_dir, remote_host, log_dir))


def run(args):
    if args.get("which") != "runbms":
        return False
    with tempfile.TemporaryDirectory(prefix="runbms-") as runbms_dir:
        logging.info("Temporary directory: {}".format(runbms_dir))
        if args.get("workdir"):
            args.get("workdir").mkdir(parents=True, exist_ok=True)
            runbms_dir = str(args.get("workdir").resolve())
        # Processing command lines args
        global resume
        resume = args.get("resume")
        if resume:
            run_id = resume
        else:
            prefix = args.get("id_prefix")
            run_id = getid()
            if prefix:
                run_id = "{}-{}".format(prefix, run_id)
        print("Run id: {}".format(run_id))
        log_dir = args.get("LOG_DIR") / run_id
        if not is_dry_run():
            log_dir.mkdir(parents=True, exist_ok=True)
            with (log_dir / "runbms_args.yml").open("w") as fd:
                yaml.dump(args, fd)
        N = args.get("N")
        ns = args.get("n")
        slice = args.get("slice")
        slice = [float(s) for s in slice.split(",")] if slice else []
        global skip_oom
        skip_oom = args.get("skip_oom")
        global skip_timeout
        skip_timeout = args.get("skip_timeout")
        # Load from configuration file
        global configuration
        configuration = Configuration.from_file(
            Path(os.getcwd()), args.get("CONFIG"))
        # Save metadata
        if not is_dry_run():
            with (log_dir / "runbms.yml").open("w") as fd:
                configuration.save_to_file(fd)
        configuration.resolve_class()
        # Read from configuration, override with command line arguments if
        # needed
        invocations = configuration.get("invocations")
        if args.get("invocations"):
            invocations = args.get("invocations")
        global minheap_multiplier
        minheap_multiplier = configuration.get("minheap_multiplier")
        if args.get("minheap_multiplier"):
            minheap_multiplier = args.get("minheap_multiplier")
        heap_range = configuration.get("heap_range")
        spread_factor = configuration.get("spread_factor")
        suites = configuration.get("suites")
        benchmarks = configuration.get("benchmarks")
        if benchmarks is None:
            benchmarks = {}
        configs = configuration.get("configs")
        global remote_host
        remote_host = configuration.get("remote_host")
        if not is_dry_run() and remote_host is not None:
            ensure_remote_dir(log_dir)
        global plugins
        plugins = configuration.get("plugins")
        if plugins is None:
            plugins = {}
        else:
            from running.plugin.runbms import RunbmsPlugin
            if type(plugins) is not dict:
                raise TypeError("plugins must be a dictionary")
            plugins = {k: RunbmsPlugin.from_config(
                k, v) for k, v in plugins.items()}
            for p in plugins.values():
                p.set_run_id(run_id)
                p.set_runbms_dir(runbms_dir)
                p.set_log_dir(log_dir)

        def run_hfacs(hfacs):
            logging.info("hfacs: {}".format(
                ", ".join([
                    hfac_str(hfac)
                    for hfac in hfacs
                ])
            ))
            for hfac in hfacs:
                run_one_hfac(invocations, hfac, suites, benchmarks,
                             configs, Path(runbms_dir), log_dir)
                print()

        def run_N_ns(N, ns):
            hfacs = get_hfacs(heap_range, spread_factor, N, ns)
            run_hfacs(hfacs)

        if slice:
            run_hfacs(slice)
            return True

        if N is None:
            run_one_hfac(invocations, None, suites, benchmarks,
                         configs, Path(runbms_dir), log_dir)
            return True

        if len(ns) == 0:
            fillin(run_N_ns, round(math.log2(N)))
        else:
            run_N_ns(N, ns)

        return True
