# `runbms`
This subcommand runs benchmarks with different configs, possibly with varying heap sizes.

## Usage
```console
runbms [-h|--help] [-i|--invocations INVOCATIONS] [-s|--slice SLICE] [-p|--id-prefix ID_PREFIX] [-m|--minheap-multiplier MINHEAP_MULTIPLIER] [--skip-oom SKIP_OOM] [--skip-timeout SKIP_TIMEOUT] [--resume RESUME] [--workdir WORKDIR] LOG_DIR CONFIG [N] [n [n ...]]
```

`-h`: print help message.

`-i`: set the number of invocations.
Overrides `invocations` in the config file.

`-s`: only use the specified heap sizes.
This is a comma-separated string of integers or floating point numbers.
For each slice `s` in `SLICE`, we run benchmarks at `s * minheap`.
`N` and `n`s are ignored. 

`-p`: add a prefix to the folder names where the results are stored.
By default, the folder that stores the result is named using the host name and the timestamp.
However, you can add a prefix to the folder name to signify which experiments the results belong to.

`-m` (preview ⚠️): multiple the minheap value for each benchmark by `MINHEAP_MULTIPLIER`.
Do **NOT** use this unless you know what you are doing.
Override `minheap_multiplier` in the config file.

`--skip-oom` (preview ⚠️): skip the remaining invocations if a benchmark under a `config` has run out of memory more than `SKIP_OOM` times.

`--skip-timeout` (preview ⚠️): skip the remaining invocations if a benchmark under a `config`  has timed out more than `SKIP_TIMEOUT` times.

`--resume` (preview ⚠️): resume a previous run under `LOG_DIR/RESUME`. If a `.log.gz` already exists for a group of invocations, they will be skipped. Remember to clean up the partial `*.log` files before resuming.

`--workdir` (preview ⚠️): use the specified directory as the working directory for benchmarks.
If not specified, a temporary directory will be created under an OS-dependent location with a `runbms-` prefix.

`LOG_DIR`: where to store the results.
This is required.

`CONFIG`: the path to the configuration file.
This is required.

`N`: the number of different heap sizes to explore.
Must be powers of two.
Explore heap sizes denoted by 0, 1, ..., and `N` (`N + 1` different sizes in total).
The heap size 0 represents `1.0 * minheap`, and the heap size `N` represents `heap_range * minheap` (by default, `6.0 * minheap`).
If `N` is omitted, then the script will run benchmarks without explicit explicitly setting heap sizes, unless you specify `-s` or use a modifier that sets the heap size.

`n`: the heap sizes to explore.
Instead of exploring 0, 1, ..., and `N`, only explore the `n`s specified.

## Keys
`invocations`: see above.

`minheap_multiplier`: see above.

`heap_range`: the heap size relative to the minheap when `n = N`.

`spread_factor`: changes how 0, 1, ..., and `N` are spread out.
When `spread_factor` is zero, the differences between 0, 1, ..., and `N` are the same.
The larger the `spread_factor` is, the coarser the spacing is at the end relative to start.
Please do **NOT** change this unless you understand how it works.

`remote_host`: the remote host to `rsync` the results to.
The exact absolute path of `LOG_DIR` is used on both the local and the remote machine.

`plugins` (preview ⚠️): plugins of this command.
Must be a dictionary, similar to how modifiers are declared.

## Plugins (preview ⚠️)
### `Zulip`
Zulip integration for notifying when experiments start or end.
No message will be sent if it'a dry run.

Here is an example.
```yaml
plugins:
  zulip:
    type: Zulip
    request:
      type: private
      to: ["your user id here"]
```
#### Keys
`request`: please follow the [Zulip API documentation](https://zulip.com/api/send-message).
Note that you don't need to put in `content` here.
Please contact the administrators of your organization for your user ID.
If you use a bot user and want to post to a channel, please [subscribe the bot user to the channel so that messages can be edited](https://github.com/zulip/zulip/issues/13658#issuecomment-573959765).

`config_file`: an optional string to the path of config file.
If not specified, the default is `~/.zuliprc`.
Please make sure that this file can only be accessed by you (e.g., `chmod 600 ~/.zulip`).
If you are a moma user, please create this file on `squirrel`, and it will then be synced to other machines.
Please follow the Zulip documentation for the [syntax](https://zulip.com/api/configuring-python-bindings) of the config file and for [obtaining an API key](https://zulip.com/api/api-keys).
If you can't create a new bot, please contact the administrators of your organization.

### `CopyFile`
Copying files from the working directory.

Here is an example.
```yaml
plugins:
  dacapo_latency:
    type: CopyFile
    patterns:
      - "scratch/dacapo-latency-*.csv"
```
#### Keys
`patterns`: a list of patterns following the Python 3 `pathlib.Path.glob` [syntax](https://docs.python.org/3/library/pathlib.html#pathlib.Path.glob).
Files matched the patterns will be copied to `LOG_DIR` where different subfolders will be created for each invocation.

`skip_failed`: don't copy files from failed runs. The default value is true.

## Interpreting the Outputs
Under construction 🚧.
### Console Outputs

### Log directory

## Heap Size Calculations
Please refer to the source code like [here](https://github.com/anupli/running-ng/blob/master/running/command/runbms.py#L47) and [here](https://github.com/anupli/running-ng/blob/master/running/command/fillin.py#L5) for the actual algorithm.

But the basic idea is as follow.
First, we start with the ends and the middle and gradually fill the gap.
This is to make sure you can see the big picture trend.
Second, the difference between sizes are smaller for smaller sizes and larger for large sizes, because the performance is much more sensitive to the change in heap sizes when the heap is small.

## Best Practices
Under construction 🚧.

### Continuously Monitor Your Experiments
The results are `rsync`ed to `remote_host` once all invocations for a benchmark at a heap size are finished.
You shouldn't log into the experiment machine so not to disturb the experiments.
You should log into the remote host and check the `LOG_DIR` there and see the new results that came in.
