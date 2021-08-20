# Quickstart
This guide will show you how to use `running-ng` to compare two different builds of JVMs.

## Installation
Please follow the [installation guide](./install.md) to install `running-ng`.
You will need Python 3.6+.

Then, create a file `two_builds.yml` with the following content.
```yaml
includes:
  - "/path/to/running-ng/config/base/runbms.yml"
```
The [YAML file](./references/index.md) represents a dictionary (key-value pairs) that defines the experiments you are running.
The `includes` directive here will populate the dictionary with some default values shipped with `running-ng`.

## Prepare Benchmarks
Add the following to `two_builds.yml`.
```yaml
benchmarks:
  dacapochopin-69a704e:
    - avrora
    - batik
    - biojava
    - cassandra
    - eclipse
    - fop
    - graphchi
    - h2
    - h2o
    - jme
    - jython
    - luindex
    - lusearch
    - pmd
    - sunflow
    - tradebeans 
    - tradesoap
    - tomcat
    - xalan
    - zxing
```
This specify a list of benchmarks used in this experiment from the [benchmark suite](./references/suite.md) `dacapochopin-69a704e`.
The benchmark suite is defined in `/path/to/running-ng/config/base/dacapo.yml`.
The `minheap` value of `dacapochopin-69a704e` is measured with AdoptOpenJDK 11 using G1 GC.

Then, add the following to `two_builds.yml`.
```yaml
overrides:
  "suites.dacapochopin-69a704e.timing_iteration": 5
  "suites.dacapochopin-69a704e.callback": "probe.DacapoChopinCallback"
```
That is, we want to run five iterations for each invocation, and use `DacapoChopinCallback` because it is the appropriate callback for this release of DaCapo.

## Prepare Your Builds
In this guide, we assume you use [`mmtk-openjdk`](https://github.com/mmtk/mmtk-openjdk).
Please follow its build guide.

I assume you produced two different builds you want to compare.
Add the following to `two_builds.yml`.
```yaml
runtimes:
  build1:
    type: OpenJDK
    release: 11
    home: "/path/to/build1/jdk" # make sure /path/to/build1/jdk/bin/java exists
  build2:
    type: OpenJDK
    release: 11
    home: "/path/to/build2/jdk" # make sure /path/to/build2/jdk/bin/java exists
```
This defines two builds of [runtimes](./references/runtime.md).

I strongly recommend you rename the builds (both the name in the configuration file and the folder name) to something more sensible, preferably with the commit hash for easy troubleshooting and performance debugging later.

## Prepare Probes
Please clone [`probes`](https://github.com/anupli/probes), and run `make`.

Add the following to `two_builds.yml`.
```yaml
modifiers:
  probes_cp:
    type: JVMClasspath
    val: "/path/to/probes /path/to/probes/probes.jar"
  probes:
    type: JVMArg
    val: "-Djava.library.path=/path/to/probes -Dprobes=RustMMTk"
```
This defines two [modifiers](./references/modifier.md), which will be used later to modify the JVM command line arguments.

## Prepare Configs
Finally, add he following to `two_builds.yml`.
```yaml
configs:
  - "build1|ms|s|c2|mmtk_gc-SemiSpace|tph|probes_cp|probes"
  - "build2|ms|s|c2|mmtk_gc-SemiSpace|tph|probes_cp|probes"
```
The syntax is described [here](./references/index.md#configs).

## Sanity Checks
The basic form of usage looks like this.
```console
running runbms /path/to/log two_builds.yml 8
```
That is, run the experiments as specified by `two_builds.yml`, store the results in `/path/to/log`, and explore eight different heap sizes (with careful arrangement of which size to run first and which to run later).

See [here](./commands/runbms.md) for a complete reference of `runbms`.

### Dry run
A dry run (by supplying `-d` to `running` **NOT** `runbms`) allows you to see the commands to be executed.
```console
running -d runbms /path/to/log two_builds.yml 8 -i 1
```
Make sure it looks like what you want.

### Single Invocation
Now, actually run the experiment, but only for one invocation (by supplying `-i 1` to `runbms`).
```console
running runbms /path/to/log two_builds.yml 8 -i 1
```
This allows you to see any issue before wasting several days only realizing that something didn't work.

## Run It
Once you are happy with everything, run the experiments.
```console
running runbms /path/to/log two_builds.yml 8 -p "two_builds"
```
Don't forget to give the results folder a prefix so that you can later tell what the experiment was for.

### Analysing Results
This is outside the scope of this quickstart guide.
