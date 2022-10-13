# Benchmark Suite

## `BinaryBenchmarkSuite`  (preview ⚠️)
A `BinaryBenchmarkSuite` is a suite of programs which can be used to run binary
benchmarks such as for C/C++ benchmarking.

### Keys
`programs`: A yaml list of benchmarks in the format:
```yaml
programs:
  <BM_NAME_1>:
    path: /full/path/to/benchmark/binary_1
    args: "Any arguments to binary_1"
  <BM_NAME_2>:
    path: /full/path/to/benchmark/binary_2
    args: "Any arguments to binary_2"
  [...]
```

A possible use-case could use wrapper shell scripts around the benchmark to
output timing and other information in a tab-separated table.

## `DaCapo`
[DaCapo benchmark suite](http://dacapo-bench.org/).
### Keys
`release`: one of the possible values `["2006", "9.12", "evaluation"]`.
The value is required.

`path`: path to the DaCapo `jar`.
The value is required.

`minheap`: a string that selects one of the `minheap_values` sets to use.

`minheap_values`: a dictionary containing multiple named sets of minimal heap sizes that is enough for a benchmark from the suite to run without triggering `OutOfMemoryError`.
Each size is measured in MiB.
The default value is an empty dictionary.
The minheap values are used only when running `runbms` with a valid `N` value.
If the minheap value for a benchmark is not specified, a default of `4096` is used.
An example looks like this.
```yaml
minheap_values:
  adoptopenjdk-15-G1:
    avrora: 7
    batik: 253
  temurin-17-G1:
    avrora: 7
    batik: 189
```

`timing_iteration`: specifying the timing iteration.
It can either be a number, which is passed to DaCapo as `-n`, or a string `converge`.
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

`companion` (preview ⚠️): the syntax is similar to `wrapper`.
The companion program will start before the main program and run in a separate terminal.
The main program will start two seconds after the companion program to make sure the companion is fully initialized.
Once the main program finishes, `^C` is sent to the terminal to stop the companion program.
Here is an example of using `companion` to launch `bpftrace` in the background to count the system calls.
```yaml
includes:
  - "$RUNNING_NG_PACKAGE_DATA/base/runbms.yml"

overrides:
  "suites.dacapo2006.timing_iteration": 1
  "suites.dacapo2006.companion": "sudo bpftrace -e 'tracepoint:raw_syscalls:sys_enter { @syscall[args->id] = count(); @process[comm] = count();} END { printf(\"Goodbye world!\\n\"); }'"
  "invocations": 1

benchmarks:
  dacapo2006:
    - fop

configs:
  - "temurin-17"
```
In the log file, the output from the main program and the output from the companion program is separated by `*****`.
A companion program should shutdown cleanly upon receiving `SIGINT` (Ctrl-C).
In the case of `bpftrace`, one should avoid using `exit()`.
Otherwise, a `SIGINT` during `exit()` will stop printing the rest of the maps, resulting in data loss.

`size`: specifying the size of input data.
Note that the names of the sizes are subject to change depending on the DaCapo releases.
The default value is `default`.

### Benchmark Specification
Some of the suite-wide keys can be overridden in a per-benchmark-basis.
The keys currently supported are `timing_iteration`, `size`, and `timeout`.
Note that, within a suite, your choice of `name` should uniquely identify a particular way of running a benchmark of name `bm_name`.
The `name` is used to get the minheap value, etc., which can depend of the size of input data and/or the timing iteration.
Therefore, it is highly recommended that you give a `name` different from the `bm_name`.

Note that, you might need to adjust various other values, including but not limit to the minheap value dictionary and the modifier exclusion dictionary.

The following is an example.
```yaml
benchmarks:
  dacapo2006:
    - {name: eclipse_large, bm_name: eclipse, size: large}
```

## `SPECjbb2015` (preview ⚠️)
[SPECjbb2015](https://www.spec.org/jbb2015/).

### Keys
`release`: one of the possible values `["1.03"]`.
The value is required.

`path`: path to the `jar`.
The value is required.
Note that the property file should reside in `path/../config/specjbb2015.props` per the standard folder structure of the ISO image provided by SPEC.

### Benchmark Specification
Only strings are allowed, which should correspond to the the mode of the SPECjbb2015 controller.
Right now, only `"composite"` is supported.

## `SPECjvm98` (preview ⚠️)
[SPECjvm98](https://www.spec.org/jvm98/).

Note that you will need to prepend probes to the classpaths, so that the [modified](https://github.com/anupli/probes/blob/master/SpecApplication.java) `SpecApplication` can be used.

Here is an example configuration file.
```yaml
includes:
  - "/home/zixianc/running-ng/src/running/config/base/runbms.yml"

modifiers:
  probes_cp:
    type: JVMClasspathPrepend
    val: "/home/zixianc/MMTk-Dev/evaluation/probes /home/zixianc/MMTk-Dev/evaluation/probes/probes.jar"

benchmarks:
  specjvm98:
    - _213_javac

configs:
  - "adoptopenjdk-8|probes_cp"
```

### Keys
`release`: one of the possible values `["1.03_05"]`.
The value is required.

`path`: path to the SPECjvm98 folder, where you can find `SpecApplication.class`.
The value is required.

`timing_iteration`: specifying the timing iteration.
It can only be a number, which is passed to SpecApplication as `-i`.
The value is required.

### Benchmark Specification
Only strings are allowed, which should correspond to benchmark program of SPECjvm98.
The following are the benchmarks:
- _200_check
- _201_compress
- _202_jess
- _209_db
- _213_javac
- _222_mpegaudio
- _227_mtrt
- _228_jack

## `Octane` (preview ⚠️)
### Keys
`path`: path to the Octane benchmark folder.
The value is required.

`wrapper`: path to the Octane wrapper written by Wenyu Zhao.
The value is required.

`timing_iteration`: specifying the timing iteration using an integer.
The value is required.

`minheap`: a string that selects one of the `minheap_values` sets to use.

`minheap_values`: a dictionary containing multiple named sets of minimal heap sizes that is enough for a benchmark from the suite to run without triggering `Fatal javascript OOM in ...`.
Each size is measured in MiB.
The default value is an empty dictionary.
The minheap values are used only when running `runbms` with a valid `N` value.
If the minheap value for a benchmark is not specified, a default of `4096` is used.
An example looks like this.
```yaml
minheap_values:
  d8:
    octane:
      box2d: 5
      codeload: 159
      crypto: 3
```
