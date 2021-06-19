from copy import deepcopy
from pathlib import Path
import shutil
import gzip
import enum
from typing import Callable, Dict, List
import functools
import re


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
    f.add_argument("FOLDER", type=Path)


def filter_stats(predicate: Callable[[str], bool]):
    def inner(stats: Dict[str, dict]):
        return {k: v for (k, v) in stats.items() if predicate(k)}
    return inner


def reduce_stats(pattern: str, new_column: str, func):
    compiled = re.compile(pattern)

    def inner(stats: Dict[str, dict]):
        to_reduce = [v for (k, v) in stats.items() if compiled.match(k)]
        if not to_reduce:
            return stats
        new_stats = deepcopy(stats)
        new_stats[new_column] = functools.reduce(func, to_reduce)
        return new_stats
    return inner


def sum_perf_event(event_name):
    pattern = "work\\.\\w+\\.{}\\.total".format(event_name)
    new_column = "work.{}.total".format(event_name)
    return reduce_stats(pattern, new_column, lambda x, y: x + y)


def ratio_perf_event(event_name: str):
    pattern = "work\\.\\w+\\.{}\\.total".format(event_name)
    aggregated_column = "work.{}.total".format(event_name)
    compiled = re.compile(pattern)

    def inner(stats: Dict[str, dict]):
        new_stats = deepcopy(stats)
        for (k, v) in stats.items():
            if compiled.match(k):
                new_column = k.replace(".total", ".ratio")
                new_stats[new_column] = v / stats[aggregated_column]
        return new_stats
    return inner


def calc_ipc(stats: Dict[str, dict]):
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


def process_lines(lines: List[str]):
    new_lines = []
    editing = EditingMode.NotEditing
    names = []
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
            event_names = "PERF_COUNT_HW_CPU_CYCLES,0,-1;PERF_COUNT_HW_INSTRUCTIONS,0,-1;PERF_COUNT_HW_CACHE_LL:MISS,0,-1;PERF_COUNT_HW_CACHE_L1D:MISS,0,-1;PERF_COUNT_HW_CACHE_DTLB:MISS,0,-1"
            event_names = list(
                map(lambda x: x.split(",")[0], event_names.split(";")))
            more_event_names = "MEM_INST_RETIRED:ALL_LOADS,0,-1;MEM_INST_RETIRED:ALL_STORES,0,-1"
            more_event_names = list(
                map(lambda x: x.split(",")[0], more_event_names.split(";")))
            event_names.extend(more_event_names)
            fs = []
            for e in event_names:
                fs.append(sum_perf_event(e))
                fs.append(ratio_perf_event(e))
                fs.append(calc_ipc)
            fs.append(filter_stats(lambda n: (
                "INSTRUCTIONS_PER_CYCLE" in n or "ratio" in n)))
            new_stats = functools.reduce(
                lambda accum, val: val(accum), fs, stats)
            if len(new_stats):
                new_stat_list = list(new_stats.items())
                new_stat_list.sort(key=lambda x: (x[0].split(".")[-2], -x[1]))
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


def process_one_file(logfile: Path):
    original = logfile.with_suffix(".gz.bak")
    if not original.exists():
        shutil.copy2(str(logfile), str(original))
    # XXX DO NOT COPY the content of the log file
    # Tab might not be preserved (especially around line breaks)
    # https://unix.stackexchange.com/questions/324676/output-tab-character-on-terminal-window
    with gzip.open(original, "rt") as old:
        with gzip.open(logfile, "wt") as new:
            new.writelines(process_lines(old.readlines()))


def process(folder: Path):
    for file in folder.glob("*.log.gz"):
        process_one_file(file)


def run(args):
    if args.get("which") != "preproc":
        return False
    process(args.get("FOLDER"))
    return True
