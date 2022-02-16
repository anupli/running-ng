# `minheap`
This subcommand runs benchmarks with different [configs](../references/index.md)
while varying heap sizes in a binary search fashion in order to determine the
minimum heap required to run each benchmark.

The result is stored in a YAML file.
The dictionary keys are encoded config strings.
For each config, there is one dictionary per benchmark suite, where the minimum heap size for each benchmark is stored.
An example is as follows.
```yaml
temurin-17.openjdk_common.hotspot_gc-G1:
  dacapochopin-69a704e:
    avrora: 7
    batik: 189
temurin-17.openjdk_common.hotspot_gc-Parallel:
  dacapochopin-69a704e:
    avrora: 5
    batik: 235
```

At the end of each run, `minheap` will print out the configuration that achieves the smallest minheap size for most benchmarks.
The minheap values for that configuration will be printed out, which can then be used to populate the minheap values a benchmark suite, such as a [DaCapo benchmark suite](../references/suite.md#dacapo).
An example is as follows.
```console
temurin-17.openjdk_common.hotspot_gc-G1 obtained the most number of smallest minheap sizes: 8
Minheap configuration to be copied to runbms config files
dacapochopin-69a704e:
  avrora: 7
  batik: 189
  biojava: 95
  eclipse: 411
  fop: 15
  graphchi: 255
  h2: 773
  jme: 29
  jython: 25
  luindex: 42
  lusearch: 21
  pmd: 156
  sunflow: 29
  tomcat: 21
  tradebeans: 131
  tradesoap: 103
  xalan: 8
  zxing: 97
```

## Usage
```console
minheap [-h] [-a|--attempts ATTEMPTS] CONFIG RESULT
```

`-h`: print help message.

`-a`  (preview ⚠️): set the number of attempts.
Overrides `attempts` in the config file.

`CONFIG`: the path to the configuration file.
This is required.

`RESULT`: where to store the results.
This file contains both the interim results and the final result.
An interrupted execution can be resumed by using the same `RESULT` path.
This is required.

## Keys
`maxheap`: the upper bound of the search.

`attempts` (preview ⚠️): for a particular heap size, if an invocation passes or fails with OOM (timeout treated as OOM), the binary search will continue with the next appropriate heap size.
If an invocation crashes and if the total number of invocations has not exceeded `ATTEMPTS`, the same heap size will be repeated.
If all `ATTEMPTS` invocations crash, the binary search for this config will stop, and `minheap` will report `inf`.
