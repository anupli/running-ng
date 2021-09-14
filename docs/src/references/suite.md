# Benchmark Suite

## `BinaryBenchmarkSuite`  (preview ⚠️)

## `DaCapo`
[DaCapo benchmark suite](http://dacapo-bench.org/).
### Keys
`release`: one of the possible values `["2006", "9.12", "evaluation"]`.
The value is required.

`path`: path to the DaCapo `jar`.
The value is required.

`minheap`: a dictionary containing the minimal heap size in megabytes to execute a benchmark from the suite without triggering `OutOfMemoryError`.
The default value is an empty dictionary.
The minheap values are used only when running `runbms` with a valid `N` value.
If the minheap value for a benchmark is not specified, a default of `4096` is used.

`timing_iteration`: specifying the timing iteration.
The value is passed to DaCapo as `-n`.
The default value is 3.

`callback`: the class (possibly within some packages) for the DaCapo callback. The value is passed to DaCapo as `-c`.
The default value is `null`.

`timeout`: timeout for one invocation of a benchmark in seconds.
The default value is `null`.

`wrapper` (preview ⚠️): specifying a wrapper (i.e., extra stuff on the command line before `java`) when running benchmarks.
The default value is `null`, a no-op.
There are two possible ways to specify `wrapper`.
First, a single string with [shell-like syntax](https://docs.python.org/3/library/shlex.html#shlex.split).
Multiple arguments are space separated.
This wrapper is used for all benchmarks in the benchmark suite.
Second, a dictionary of strings with shell-like syntax to specify possibly different wrappers for different benchmarks.
If a benchmark doesn't have a wrapper in the dictionary, it is treated as `null`.
