# `minheap`
This subcommand runs benchmarks with different [configs](./references/index.md)
while varying heap sizes in a binary search fashion in order to determine the
minimum heap required to run each benchmark.

The output is stored as a yaml file which can then be directly used as an
[override](./references/index.md#overrides) for minheap values for a benchmark
suite.

## Usage
```console
minheap [-h|--help] CONFIG RESULT
```

`-h`: print help message.

`CONFIG`: the path to the configuration file.
This is required.

`RESULT`: where to store the results.
This is required.
