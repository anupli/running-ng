# Design Principles
## Sound methodology
Sound methodology is crucial for the type of performance analysis work we do.
Please see the documentation for each of the command for details.
We also try to include sensible default values in the base configuration files.

## Reproducibility
It should be easy to reproduce a set of experiments.
To this end, various commands will save as much metadata with the results.
For example, [`runbms`](../commands/runbms.md) saves the flattened configuration file and command line arguments in the results folder.
For each log, basic information about the execution environment, such as `uname`, the model name of the CPU, and frequencies of CPU cores, is saved as well.

## Extensibility
Broadly, the project consists of two parts: the core and the commands.
The core provides abstractions for core concepts, such as benchmarks and execution environments, and can be extended through class inheritance.

The commands are the user-facing parts that uses the core to provide concrete functionalities.

## Reusability
The configuration files can be easily reused through the `includes` and `overrides` mechanisms.
For example, people might want to run multiple sets of experiments with minor tweaks, and being able to share a common base configuration file is ergonomic.
This is also crucial to the first point that people can get a set of sensible default values by including base configuration files shipped with the project.

## Human-readable syntax
We use YAML as the format for the configuration files.
Please read the [syntax reference](../references/index.md) for more details.
