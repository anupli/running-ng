#!/usr/bin/env python3
import glob
import gzip
import os
import shutil
import subprocess
import sys

ADVICE_EXTS = ["ca", "dc", "ec"]
advice_folder = sys.argv[1]


JikesRVM_HEADER = (
    "============================ MMTk Statistics Totals ============================"
)
JikesRVM_FOOTER = (
    "------------------------------ End MMTk Statistics -----------------------------"
)


def extract_blocks(lines, header, footer):
    lines = [line.decode("ascii") for line in lines]
    i = 0
    blocks = []
    while i < len(lines):
        if header in lines[i]:
            i += 1
            block = []
            while footer not in lines[i]:
                block.append(lines[i])
                i += 1
            blocks.append(block)
        i += 1
    return blocks


def cleanse(filename):
    sed_pattern = "s/{urls[^}]*}//g"
    if sys.platform == "linux" or sys.platform == "linux2":
        cmd = ["sed", "-i", sed_pattern, filename]
    elif sys.platform == "darwin":
        cmd = ["sed", "-i", "", sed_pattern, filename]
    print("run({})".format(" ".join(cmd)))
    subprocess.run(cmd)


def select_best_invocation(scenario):
    filename = f"{scenario}.log.gz"
    metrics = []
    with gzip.open(os.path.join(advice_folder, filename)) as log_file:
        stats_blocks = extract_blocks(log_file, JikesRVM_HEADER, JikesRVM_FOOTER)
        for stats_block in stats_blocks:
            stats = dict(zip(stats_block[0].split("\t"), stats_block[1].split("\t")))
            metrics.append(float(stats["time.gc"]) + float(stats["time.mu"]))
    if not metrics:
        print("No metric is found")
        return -1
    print(f"Metrics for {scenario}: {metrics}")
    _, idx = min([(val, idx) for (idx, val) in enumerate(metrics)])
    return idx


def select_advice_file(scenario, best_invocation):
    if not best_invocation >= 0:
        return
    benchmark_name = scenario.split(".")[0]
    for ext in ADVICE_EXTS:
        src = f"{scenario}.{best_invocation}.{ext}"
        src = os.path.join(advice_folder, src)
        dst = f"{benchmark_name}.{ext}"
        dst = os.path.join(advice_folder, dst)
        print(f"Copying {src} to {dst}")
        shutil.copyfile(src, dst)
        cleanse(dst)


def main():
    scenario_logs = glob.glob(os.path.join(advice_folder, "*.log.gz"))
    scenarios = [os.path.basename(s).replace(".log.gz", "") for s in scenario_logs]
    print(f"Found scenarios {scenarios}")
    for scenario in scenarios:
        print(f"Processing scenario {scenario}")
        best_invocation = select_best_invocation(scenario)
        print(f"Best invocation for scenario {scenario} is {best_invocation}")
        select_advice_file(scenario, best_invocation)


if __name__ == "__main__":
    main()
