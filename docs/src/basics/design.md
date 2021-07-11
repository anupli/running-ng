# Design Principles
## Sound methodology
Sound methodology is crucial for the type of performance analysis work we do.
Please see the documentation for each of the command for details.
We also try to include sensible default values in the base configuration files.

## Reproducibility
It should be easy to reproduce a set of experiments.
To this end, various commands will save as much metadata with the results.
For example, [`runbms`](./commands/runbms.md) saves the flatten configuration file and command line arguments in the results folder.
For each log, basic information about the execution environment, such as `uname`, the model name of the CPU, and frequencies of CPU cores, is saved as well.

## Extensibility

## Reusability

## Human-readable syntax
We use YAML as the format for the configuration files.
Please read the [syntax reference]() for more details.