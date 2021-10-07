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
    val: "/home/zixianc/MMTk-Dev/evaluation/probes/libperf_statistics.so"
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
