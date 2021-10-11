# Whole-Process Performance Event Monitoring
## JVMTI
Please clone and build [`probes`](../quickstart.md#prepare-probes).

Under the `probes` folder, you will find a JVMTI agent, `libperf_statistics.so`.
You can check the source code [here](https://github.com/anupli/probes/blob/master/native/jvmti_agents/perf_statistics.c).
To use the agent, there are four things you need to do.

First, you will need to tell the dynamic linker to load the shared library before the VM boots.
This ensures that the `inherit` flag of `perf_event_attr` works properly and all child threads subsequently spawned are included in the results.
```yaml
modifiers:
  jvmti_env:
    type: EnvVar
    var: "LD_PRELOAD"
    val: "/path/to/probes/libperf_statistics.so"
```

Second, you need to specify a list of events you want to measure.
```yaml
modifiers:
  perf:
    type: EnvVar
    var: "PERF_EVENTS"
    val: "PERF_COUNT_HW_CPU_CYCLES,PERF_COUNT_HW_INSTRUCTIONS,PERF_COUNT_HW_CACHE_LL:MISS,PERF_COUNT_HW_CACHE_L1D:MISS,PERF_COUNT_HW_CACHE_DTLB:MISS"
```
If you want to get a full list of events you can use on a particular machine, you can clone and build [`libpfm4`](https://sourceforge.net/p/perfmon2/libpfm4/ci/master/tree/) and run the `showevtinfo` [program](https://sourceforge.net/p/perfmon2/libpfm4/ci/master/tree/examples/showevtinfo.c).

Third, you need to tell the JVM to load the agent.
Note that you need to specify the absolute path.
```yaml
modifiers:
  jvmti:
    type: JVMArg
    val: "-agentpath:/path/to/probes/libperf_statistics.so"
```

Finally, you need to let the DaCapo benchmark inform the start and the end of a benchmark iteration.
We will reuse the `RustMMTk` probe here, as the callback functions in the JVMTI agent are also called `harness_begin` and `harness_end`.
```yaml
modifiers:
  probes_cp:
    type: JVMClasspath
    val: "/path/to/probes /path/to/probes/probes.jar"
  probes:
    type: JVMArg
    val: "-Djava.library.path=/path/to/probes -Dprobes=RustMMTk"
```

Now, putting it all together, you can define a set of modifiers, and use that set in your config strings.
```yaml
modifiers:
  jvmti_common:
    type: ModifierSet
    val: "probes|probes_cp|jvmti|jvmti_env|perf"
```

## MMTk
Please clone and build [`probes`](../quickstart.md#prepare-probes).
You will need to build `mmtk-core` with the `perf_counter` feature.

First, you need to let the DaCapo benchmark inform the start and the end of a benchmark iteration.
```yaml
modifiers:
  probes_cp:
    type: JVMClasspath
    val: "/path/to/probes /path/to/probes/probes.jar"
  probes:
    type: JVMArg
    val: "-Djava.library.path=/path/to/probes -Dprobes=RustMMTk"
```

Then, you can specify a list of events you want to measure.
```yaml
modifiers:
  mmtk_perf:
    type: EnvVar
    var: "MMTK_PHASE_PERF_EVENTS"
    val: "PERF_COUNT_HW_CPU_CYCLES,0,-1;PERF_COUNT_HW_INSTRUCTIONS,0,-1;PERF_COUNT_HW_CACHE_LL:MISS,0,-1;PERF_COUNT_HW_CACHE_L1D:MISS,0,-1;PERF_COUNT_HW_CACHE_DTLB:MISS,0,-1"
```
Note that the list is semicolon-separated.
Each entry consists of three parts, separated by commas.
The first part is the name of the event.
Please refer to the previous section for details.
The second part and the third part are `pid` and `cpu`, per `man perf_event_open`.
In most cases, you want to use `0,-1`, that is measuring the calling thread (the results will be combined later through the `inherit` flag) on any CPU.
For some events, such as RAPL, only package-wide measurement is supported, and you will have to adjust the values accordingly.

**Note that you might have to increase the value of `MAX_PHASES` in `crate::util::statistics::stats` to a larger value, e.g., `1 << 14`, so that the array storing the per-phase value will not overflow.**

# Work-Packet Performance Event Monitoring
It's similar to the whole-process performance event monitoring for MMTk.
Just use `MMTK_WORK_PERF_EVENTS` instead of `MMTK_PHASE_PERF_EVENTS`.

# Machine-Specific Notes
On Xeon D-1540 Broadwell (`mole` and `vole`), the `PERF_COUNT_HW_CACHE_LL:MISS` event is always zero.
```console
perf stat -e LLC-load-misses,cycles /bin/ls

 Performance counter stats for '/bin/ls':

                 0      LLC-load-misses
         1,729,786      cycles

       0.001135511 seconds time elapsed

       0.001180000 seconds user
       0.000000000 seconds sys
```

On AMD machines, the `PERF_COUNT_HW_CACHE_LL:MISS` event fails to open.
`perf_event_open` syscall fails with `No such file or directory`.
