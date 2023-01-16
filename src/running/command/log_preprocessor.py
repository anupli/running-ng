from copy import deepcopy
from pathlib import Path
import gzip
import enum
from typing import Any, Callable, Dict, List
import functools
import re
from running.config import Configuration
import os

MMTk_HEADER = "============================ MMTk Statistics Totals ============================"
MMTk_FOOTER = "------------------------------ End MMTk Statistics -----------------------------"


class EditingMode(enum.Enum):
    NotEditing = 1
    Names = 2
    Values = 3
    TotalTime = 4


def setup_parser(subparsers):
    f = subparsers.add_parser("preproc")
    f.set_defaults(which="preproc")
    f.add_argument("CONFIG", type=Path)
    f.add_argument("SOURCE", type=Path)
    f.add_argument("TARGET", type=Path)


def filter_stats(predicate: Callable[[str], bool]):
    def inner(stats: Dict[str, float]):
        return {k: v for (k, v) in stats.items() if predicate(k)}
    return inner


def reduce_stats(pattern: str, new_column: str, func):
    compiled = re.compile(pattern)

    def inner(stats: Dict[str, float]):
        to_reduce = [v for (k, v) in stats.items() if compiled.match(k)]
        if not to_reduce:
            return stats
        new_stats = deepcopy(stats)
        new_stats[new_column] = functools.reduce(func, to_reduce)
        return new_stats
    return inner


def sum_work_perf_event(event_name):
    pattern = "work\\.\\w+\\.{}\\.total".format(event_name)
    new_column = "work.{}.total".format(event_name)
    return reduce_stats(pattern, new_column, lambda x, y: x + y)


def ratio_work_perf_event(event_name: str):
    pattern = "work\\.\\w+\\.{}\\.total".format(event_name)
    aggregated_column = "work.{}.total".format(event_name)
    compiled = re.compile(pattern)

    def inner(stats: Dict[str, float]):
        new_stats = deepcopy(stats)
        for (k, v) in stats.items():
            if compiled.match(k):
                new_column = k.replace(".total", ".ratio")
                new_stats[new_column] = v / stats[aggregated_column]
        return new_stats
    return inner


def ratio_event(event_name: str):
    def inner(stats: Dict[str, float]):
        new_stats = deepcopy(stats)
        stw_key = "{}.stw".format(event_name)
        other_key = "{}.other".format(event_name)
        if stw_key in stats and other_key in stats:
            gc = stats[stw_key]
            mu = stats[other_key]
            total = gc + mu
            new_stats["{}.ratio".format(stw_key)] = gc / total
            new_stats["{}.ratio".format(other_key)] = mu / total
        return new_stats
    return inner


def calc_ipc(stats: Dict[str, float]):
    new_stats = deepcopy(stats)
    for phase in ["mu", "gc"]:
        inst = stats.get("PERF_COUNT_HW_INSTRUCTIONS.{}".format(phase))
        cycles = stats.get("PERF_COUNT_HW_CPU_CYCLES.{}".format(phase))
        if inst is not None and cycles is not None:
            if cycles == 0:
                assert inst == 0
                continue
            new_stats["INSTRUCTIONS_PER_CYCLE.{}".format(
                phase)] = inst / cycles
    return new_stats


def calc_work_ipc(stats: Dict[str, float]):
    pattern = "work\\.\\w+\\.PERF_COUNT_HW_INSTRUCTIONS\\.total"
    compiled = re.compile(pattern)
    new_stats = deepcopy(stats)
    for (k, v) in stats.items():
        if compiled.match(k):
            cycles = k.replace("PERF_COUNT_HW_INSTRUCTIONS",
                               "PERF_COUNT_HW_CPU_CYCLES")
            ipc = k.replace("PERF_COUNT_HW_INSTRUCTIONS.total",
                            "INSTRUCTIONS_PER_CYCLE.ratio")
            new_stats[ipc] = stats[k] / stats[cycles]
    return new_stats


def stat_sort_helper(key: str, value: float):
    if len(key.split(".")) > 1:
        return key.split(".")[-2], -value
    else:
        return key, -value


def process_lines(configuration: Configuration, lines: List[str]):
    new_lines = []
    editing = EditingMode.NotEditing
    names = []
    funcs: List[Any]
    funcs = []
    if configuration.get("preprocessing") is None:
        funcs = []
    else:
        for f in configuration.get("preprocessing"):
            if f["name"] == "sum_work_perf_event":
                for v in f["val"].split(","):
                    funcs.append(sum_work_perf_event(v))
            elif f["name"] == "ratio_work_perf_event":
                for v in f["val"].split(","):
                    funcs.append(ratio_work_perf_event(v))
            elif f["name"] == "calc_work_ipc":
                funcs.append(calc_work_ipc)
            elif f["name"] == "ratio_event":
                for v in f["val"].split(","):
                    funcs.append(ratio_event(v))
            elif f["name"] == "filter_stats":
                patterns_to_keep = f["val"].split(",")
                funcs.append(filter_stats(lambda n: any(
                    [p in n for p in patterns_to_keep])))
            elif f["name"] == "calc_ipc":
                funcs.append(calc_ipc)
            else:
                raise ValueError("Not supported preprocessing functionality")
    for line in lines:
        if line.strip() == MMTk_HEADER:
            new_lines.append(line)
            editing = EditingMode.Names
            continue
        elif line.strip() == MMTk_FOOTER:
            assert editing == EditingMode.TotalTime
            new_lines.append(line)
            editing = EditingMode.NotEditing
            continue
        if editing == EditingMode.Names:
            names = line.strip().split("\t")
            editing = EditingMode.Values
        elif editing == EditingMode.Values:
            values = map(float, line.strip().split("\t"))
            stats = dict(zip(names, values))
            new_stats = functools.reduce(
                lambda accum, val: val(accum), funcs, stats)
            if len(new_stats):
                new_stat_list = list(new_stats.items())
                new_stat_list.sort(key=lambda x: stat_sort_helper(x[0], x[1]))
                new_names, new_values = list(zip(*new_stat_list))
                new_lines.append("{}\n".format("\t".join(new_names)))
                new_lines.append("{}\n".format(
                    "\t".join(map(str, new_values))))
            else:
                new_lines.append("empty_after_preprocessing\n")
                new_lines.append("0\n")
            editing = EditingMode.TotalTime
        elif editing == EditingMode.TotalTime:
            new_lines.append(line)
        else:
            new_lines.append(line)

    return new_lines


def process_one_file(configuration: Configuration, original: Path, targetfile: Path):
    # XXX DO NOT COPY the content of the log file
    # Tab might not be preserved (especially around line breaks)
    # https://unix.stackexchange.com/questions/324676/output-tab-character-on-terminal-window
    with gzip.open(original, "rt") as old:
        with gzip.open(targetfile, "wt") as new:
            new.writelines(process_lines(configuration, old.readlines()))


def process(configuration: Configuration, source: Path, target: Path):
    for file in source.glob("*.log.gz"):
        process_one_file(configuration, file, target / file.name)


def run(args):
    if args.get("which") != "preproc":
        return False
    configuration = Configuration.from_file(
        Path(os.getcwd()), args.get("CONFIG"))
    source = args.get("SOURCE")
    target = args.get("TARGET")
    target.mkdir(parents=True, exist_ok=True)
    process(configuration, source, target)
    return True
