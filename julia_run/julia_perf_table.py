import os
import re
import sys
import pandas as pd
import numpy as np
from scipy import stats

# NORMALIZE_TO = "julia-stock(0.0x minheap,.gcthreads-16)"
NORMALIZE_TO = None

# Regular expressions to find the benchmark name and the table data
bench_regex = re.compile(r'bench = "(.*).jl"')
table_regex = re.compile(r'\│ (minimum|median|maximum|stdev) \│\s*([\d\.NaN]+) \│\s*([\d\.NaN]+) \│\s*([\d\.NaN]+) \│\s*([\d\.NaN]+) \│\s*([\d\.NaN]+) \│\s*([\d\.NaN]+) \│\s*([\d\.NaN]+) \│\s*([\d\.NaN]+) \│')
file_name_regex = re.compile(r'^(.*?)\.(\d+)\.(\d+)\.(.*?)(\.(.*))?\.gcbenchmarks\.log$')

def extract_data_from_log_file(log_file_path):
    # Read the file
    with open(log_file_path, 'r') as file:
        log_content = file.readlines()

    # Initialize an empty DataFrame to store data
    benchmark_data = pd.DataFrame(columns=['total time', 'gc time'])

    # Go through the lines in the log content
    for line in log_content:
        table_match = table_regex.match(line)
        if table_match:
            data = [float(value) if value != 'NaN' else None for value in table_match.group(2, 3)]
            df = pd.DataFrame([data], columns=['total time', 'gc time'])
            benchmark_data = pd.concat([benchmark_data, df])

    # Get the file name from the file path
    file_name = os.path.basename(log_file_path)

    # Extract the benchmark name and the heap size factor from the file name
    match = file_name_regex.match(file_name)
    benchmark_name_from_file = match.group(1) if match else None
    heap_size_factor = int(match.group(2))/1000 if match else None  # convert to the multiplier form
    build_name = match.group(4) if match else None

    other_configs = match.group(5) if match else None
    if other_configs is None:
        other_configs_str = ""
    else:
        other_configs_str = ",{}".format(other_configs)

    # Calculate the average of total time and gc time
    average_values = benchmark_data.mean()

    # Instead of returning a DataFrame, return the average_values Series
    return benchmark_name_from_file, f'{build_name}({heap_size_factor}x minheap{other_configs_str})', average_values

import matplotlib.pyplot as plt
import re

# Extract heap size factor from build name
def extract_heap_size(build_name):
    match = re.search(r"\((.*?)x minheap", build_name)
    if match:
        return float(match.group(1))
    else:
        return None

def plot(all_data_df):
    # Filter out rows that contain the baseline build
    df = all_data_df.copy().reset_index()
    assert(NORMALIZE_TO is not None)
    baseline_build = NORMALIZE_TO
    df = df[df['level_1'] != baseline_build]
    df.set_index(['level_0', 'level_1'], inplace=True)

    # Extract benchmarks
    benchmarks = df.index.get_level_values(0).unique()

    # Determine the layout of the subplots
    nrows = int(np.ceil(len(benchmarks) ** 0.5))
    ncols = int(np.ceil(len(benchmarks) / nrows))

    # Create a figure and axes for the subplots
    fig, axs = plt.subplots(nrows=nrows, ncols=ncols, figsize=(5*ncols, 5*nrows), constrained_layout=True)
    axs = axs.flatten()  # flatten the array of axes for easy indexing

    # Plot for each benchmark
    for i, benchmark in enumerate(benchmarks):
        ax = axs[i]  # current axis

        # Filter data for the benchmark
        df_benchmark = df.loc[benchmark]

        # Extract the build names from the index
        build_names = df_benchmark.index.map(lambda x: x.split('(')[0])

        # Group data by the build names
        grouped = df_benchmark.groupby(build_names)

        # For each group, plot a line
        for build, group in grouped:
            heap_sizes = group.index.map(extract_heap_size)
            ax.plot(heap_sizes, group['total time'], marker='o', label=build)

        # Draw a dashed horizontal line for the baseline at Y=1
        ax.axhline(y=1, color='r', linestyle='--')

        # Set the limits of the x-axis
        ax.set_xlim(1, 6)
        # Set the limits of the y-axis
        ax.set_ylim(0, 2)

        ax.set_title(benchmark)
        ax.set_xlabel('Heap Size Factor')
        ax.set_ylabel('Total Time (normalized)')
        ax.legend()

    # Remove unused subplots
    for j in range(i+1, len(axs)):
        fig.delaxes(axs[j])

    # Save the entire figure to a file
    fig.savefig('output.png')  # replace 'output.png' with your preferred file name
    fig.savefig('output_hr.png', dpi=300)  # replace 'output.png' with your preferred file name
    fig.savefig('output.svg')  # replace 'output.png' with your preferred file name


def main():
    # Initialize an empty dictionary to store all data
    all_data = {}

    # Loop over all provided folder paths
    for folder_path in sys.argv[1:]:
        # Find all .log files in the folder and its subfolders
        log_files = [os.path.join(dirpath, f)
                    for dirpath, dirnames, files in os.walk(folder_path)
                    for f in files if f.endswith('.log')]

        # Loop over all .log files and extract data
        for log_file in log_files:
            benchmark_name, build_name, average_values = extract_data_from_log_file(log_file)

            # Add the average_values to the corresponding benchmark's data
            if benchmark_name not in all_data:
                all_data[benchmark_name] = {}

            dict = average_values.to_dict()
            dict['mutator time'] = dict['total time'] - dict['gc time']

            all_data[benchmark_name][build_name] = dict

    if NORMALIZE_TO is None:
        to_output = all_data
    else:
        normalized_data = {}
        for bm in all_data.keys():
            base_total_time = all_data[bm][NORMALIZE_TO]["total time"]
            base_gc_time = all_data[bm][NORMALIZE_TO]["gc time"]
            base_mutator_time = all_data[bm][NORMALIZE_TO]["mutator time"]
            assert base_total_time != 0
            assert base_gc_time != 0
            normalized_data[bm] = {}
            for build in all_data[bm].keys():
                normalized_data[bm][build] = {}
                normalized_data[bm][build]["total time"] = all_data[bm][build]["total time"] / base_total_time
                normalized_data[bm][build]["gc time"] = all_data[bm][build]["gc time"] / base_gc_time
                normalized_data[bm][build]["mutator time"] = all_data[bm][build]["mutator time"] / base_mutator_time

        to_output = normalized_data

    # Convert the dictionary to a DataFrame
    all_data_df = pd.concat({k: pd.DataFrame(v).T for k, v in to_output.items()}, axis=0)
    all_data_df = all_data_df.sort_index()

    all_data_df.round(4)

    # Print the final DataFrame
    print(all_data_df.to_markdown())

    if NORMALIZE_TO is not None:
        plot(all_data_df)

if __name__ == "__main__":
    main()

