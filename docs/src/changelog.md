# Changelog
## Unreleased
### Added

### Changed

### Deprecated

### Removed

### Fixed

### Security

## [`v0.3.7` (2023-02-14)](https://github.com/anupli/running-ng/releases/tag/v0.3.7)
### Fixed
#### Commands
- `runbms`: better heuristics to detect whether a host is in the moma subnet.

## [`v0.3.6` (2023-01-16)](https://github.com/anupli/running-ng/releases/tag/v0.3.6)
### Added
#### Base Configurations
- DaCapo Chopin Snapshot-6e411f33

### Fixed
- Fixed type annotations in untyped functions and make `Optional`s explicit.

## [`v0.3.5` (2022-10-13)](https://github.com/anupli/running-ng/releases/tag/v0.3.5)
### Changed
#### Commands
- `runbms`: when a companion program exits with a non-zero code, a warning is generated instead of an exception to prevent stopping the entire experiment.

## [`v0.3.4` (2022-10-13)](https://github.com/anupli/running-ng/releases/tag/v0.3.4)
### Fixed
#### Commands
- `runbms`: fix the file descriptor leak when running benchmarks with companion programs.

## [`v0.3.3` (2022-10-12)](https://github.com/anupli/running-ng/releases/tag/v0.3.3)
### Changed
#### Commands
- `runbms` prints out the logged in users when emitting warnings when the machine has more than one logged in users.

### Fixed
#### Modifiers
- `Companion`: skip value options expansion if no value option is provided to avoid interpreting bpftrace syntax as replacement fields.

## [`v0.3.2` (2022-10-12)](https://github.com/anupli/running-ng/releases/tag/v0.3.2)
### Added

#### Modifiers
- `Companion`

## [`v0.3.1` (2022-09-18)](https://github.com/anupli/running-ng/releases/tag/v0.3.1)
### Added
#### Base Syntax
- Use the `$RUNNING_NG_PACKAGE_DATA` environment variable to refer to base configurations shipped with running-ng, such as `$RUNNING_NG_PACKAGE_DATA/base/runbms.yml`, regardless how you installed runnin-ng.
#### Benchmark Suites
- `DaCapo` gains an extra key `companion` to facilitate eBPF tracing programs.

### Changed
- Overhauled Python packaging with PEP 517
- `zulip` is now an optional Python dependency. Use `pip install running-ng[zulip]` if you want to use the `Zulip` `runbms` plugin.

### Removed
- Dropping Python 3.6 support for users.
#### Base Configurations
- Removing AdoptOpenJDK from the base configuration files. AdoptOpenJDK is now replaced by Temurin.

## [`v0.3.0` (2022-03-19)](https://github.com/anupli/running-ng/releases/tag/v0.3.0)
### Added
#### Modifiers
- `JVMClasspathAppend`
- `JVMClasspathPrepend`

#### Benchmark Suites
- `SPECjvm98`

### Changed
#### Modifiers
- `JVMClasspath` is now an alias of `JVMClasspathAppend`. This is backward compatible.

#### Commands
- `runbms` prints out the version number of `running-ng` in log files.

### Deprecated
- Deprecating Python 3.6 support for users. Python 3.6 will NOT be supported once moma machines are upgraded to the latest Ubuntu LTS.

### Removed
- Dropping Python 3.6 support for developers (NOT users). pytest 7.1+ requires at least Python 3.7.

## [`v0.2.2` (2022-03-07)](https://github.com/anupli/running-ng/releases/tag/v0.2.2)

### Fixed
#### Benchmark Suites
- `JavaBenchmarkSuite`: Some DaCapo benchmarks refers to internal classes (e.g., under `jdk.internal.ref`), and DaCapo implemented a workaround for this behaviour in the jar. However, since we are invoking DaCapo using `-cp` and the name of the main class, that workaround is bypassed. That workaround is now reimplemented in running-ng through an extra JVM argument `--add-exports`.

## [`v0.2.1` (2022-03-05)](https://github.com/anupli/running-ng/releases/tag/v0.2.1)
### Changed
#### Commands
- `runbms` now skips printing CPU frequencies if the system doesn't support it, e.g., when using Docker Desktop on Mac.

### Fixed
#### Benchmark Suites
- `BinaryBenchmarkSuite`: fixes missing parameter when constructing `BinaryBenchmark` due to a bug in previous refactoring

## [`v0.2.0` (2022-02-20)](https://github.com/anupli/running-ng/releases/tag/v0.2.0)
### Added
#### Base Configurations
- AdoptOpenJDK 16
- DaCapo Chopin Snapshot-29a657f, Chopin Snapshot-f480064
- Temurin 8, 11, 17
- SPECjbb 2015, 1.03

#### Commands
- `minheap` gains an extra key `attempts` (can be overridden by `--attempts`) so that crashes don't cause bogus minheap measurements.
- `minheap` stores results in a YAML file, which is also used to resume an interrupted execution.
- `minheap` prints the minheap values of the best config at the ends.
- `runbms` gains an extra argument, `--resume`, to resume an interrupted execution from a log folder.
- `runbms` gains an extra argument, `--workdir`, to override the default working directory.
- `runbms` adds more information of the environment to the log file, including the date, logged in users, system load, and top processes.
- `runbms` gains a callback-based plugin system, and an extra key `plugins` is added.
- `runbms` gains a plugin `CopyFile` to copy files from the working directory.
- `runbms` gains a plugin `Zulip`, which sends messages about the progress of the experiments, and warns about reservation expiration on moma machines.
- `runbms` outputs a warning message if more than one users are logged in.
- `runbms` uses uppercase letters if there are more than 26 configs.

#### Modifiers
- `ModifierSet`
- `Wrapper`
- `JSArg`

#### Runtimes
- `D8`
- `SpiderMonkey`
- `JavaScriptCore`
- `JVM` now detects OOM generated in the form of Rust panic from `mmtk-core`.

#### Benchmark Suites
- `DaCapo` gains an extra key `size`, which is used to specify the size of the input.
- `DaCapo` now allows individual benchmark to override the timing iteration, input size, and timeout of the suite.
- `SPECjbb2015`: basic support for running SPECjbb 2015 in composite mode.
- `Octane`: basic support for running Octane using Wenyu's wrapper script.

### Changed
#### Benchmark Suites
- The `minheap` key of `DaCapo` changes from a dictionary to a string. The string is used to look up `minheap_values`, which are collections of minheap values. This makes it easier to store multiple sets of minheap values for the same benchmark suite measured using different runtimes.

#### Base Syntax
- Whitespaces can be used in config strings for visual alignment. They are ignored when parsed.

#### Commands
- The `--slice` argument of `runbms` now accepts multiple comma-separated floating point numbers. 

### Removed
#### Base Configurations
- DaCapo Chopin Snapshot-69a704e

### Fixed
#### Commands
- Resolving relative paths of runtimes before running. Otherwise, they would be resolved relative to the `runbms` working directory.
- Use the `BinaryIO` interface of file IO and interprocess communication to avoid invalid UTF-8 characters from crashing the script.
- Subprocesses now inherit environment variables from the the parent process.
- `minheap` now runs in a temporary working directory to avoid file-based conflicts between concurrent executions. Note that network-port-based conflicts can still happen.

## [`v0.1.0` (2021-08-09)](https://github.com/anupli/running-ng/releases/tag/v0.1.0)
Initial release.

### Added
#### Commands
- `fillin`
- `minheap`
- `runbms`

#### Modifiers
- `JVMArg`
- `JVMClasspath`
- `EnvVar`
- `ProgramArg`

#### Runtimes
- `NativeExecutable`
- `OpenJDK`
- `JikesRVM`

#### Benchmark Suites
- `BinaryBenchmarkSuite`
- `DaCapo`

#### Base Configurations
- AdoptOpenJDK 8, 11, 12, 13, 14, 15
- DaCapo 2006, 9.12 (Bach), 9.12 MR1, 9.12 MR1 for Java 6, Chopin Snapshot-69a704e
