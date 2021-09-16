# Command References
Please see the sections in this chapter for the references for each of the subcommands.

## Usage
```console
running [-h|--help] [-v|--verbose] [-d|--dry-run] [--version] subcommand
```

`-h`: print help message.

`-v`: use `DEBUG` for logging level.
The default logging level is `INFO`.

`-d`: enable dry run.
Each of the subcommands that respect is flag will print out the commands to be executed in a child process instead of actually executing them.

`--version`: print the version number of `running-ng`.
