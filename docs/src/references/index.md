# Configuration File Syntax
The configuration file is in YAML format.
You can find a good YAML tutorial
[here](https://docs.ansible.com/ansible/latest/reference_appendices/YAMLSyntax.html).
Below is the documentation for all the top-level keys that are common to all
commands.

## `benchmarks`
A YAML list of benchmarks to run in each specified [benchmark suite](#suites).

For example:
```yaml
benchmarks:
  dacapo2006:
    - eclipse
  dacapobach:
    - avrora
    - fop
```
specifies `running` to run the `eclipse` benchmark from the `dacapo2006`
benchmark suite; and the `avrora` and `fop` benchmarks from the `dacapobach`
benchmark suite. These benchmark suites have to be defined previously (usually
through an [`includes` key](#includes)).

Note that each benchmark of a benchmark suite can either be a string or a suite-specific dictionary.
For example, for the DaCapo benchmark suite, the following two snippets are equivalent.

```yaml
benchmarks:
  dacapo2006:
    - eclipse
```

```yaml
benchmarks:
  dacapo2006:
    - {name: eclipse, bm_name: eclipse, size: default}
```

## `configs`
A YAML list of configuration strings to be used to run the benchmarks. These are
specified as a [`runtime`](#runtimes) followed by a `'|'` separated list of
[modifiers](./modifier.md), i.e. `"<runtime>|<modifier>|...|<modifier>"`.

For example:
```yaml
configs:
  - "openjdk11|ms|s|c2"
  - "openjdk15|ms|s"
```
specifies `running` to use the `openjdk11` `runtime` with `ms`, `s`, and `c2`
modifiers; and the `openjdk15` `runtime` with the `ms`, and `s` modifiers. In
the example above, we assume that both the `runtimes` and modifiers have been
previously defined (in either the current configuration file or in an [`includes`
file](#includes)).

## `includes`
A YAML list of paths to YAML files that are to be included into the current
configuration file for definitions of some keys.

This is primarily used to provide re-usability and extensibility of
configuration files. A pre-processor step in `running` takes care of including
all the specified files. A flattened version of the final configuration file is
also generated and placed in the results folder for reproducibility.

The paths can be either absolute or relative.
Relative paths are solved relative to the current file.
For example, if `$HOME/configs/foo.yml` has an `include` line `../bar.yml`, the
line is interpreted as `$HOME/bar.yml`.
Similarly,
```yaml
includes:
 - "./base/suites.yml"
 - "./base/modifiers.yml"
```
includes the `suites.yml` and `modifiers.yml` files located at `./base`
respectively.

Any environment variable in the paths are also resolved before any further processing.
This include a special environment variable `$RUNNING_NG_PACKAGE_DATA` that allows
you to refer to various configuration files shipping with running-ng, regardless how you installed running-ng.
For example, in a global `pip` installation, `$RUNNING_NG_PACKAGE_DATA` will look like `/usr/local/lib/python3.10/dist-packages/running/config`.

## `overrides`
Under construction 🚧.

## `modifiers`
A YAML dictionary of program arguments or environment variables that are to be
used with [config strings](#configs). Cannot use `-` in the key for a modifier.
Each modifier requires a `type` key with other keys being specific to that
`type`. For more information regarding the different `type`s of modifiers,
please refer to [this page](./modifier.md).

**Warning preview feature ⚠️**. We can exclude certain benchmarks from using a
specific modifier by using an `exclude` key along with a YAML list of benchmarks
to be excluded from each benchmark suite.

For example:
```yaml
modifiers:
  s:
    type: JVMArg
    val: "-server"
  c2:
    type: JVMArg
    val: "-XX:-TieredCompilation -Xcomp"
    excludes:
      dacapo2006:
        - eclipse
```
specifies two modifiers, `s` and `c2`, both of `type`
[`JVMArg`](./modifier.md#JVMArg) with their respective values. Here, the
`eclipse` benchmark from the `dacapo2006` benchmark suite has been excluded from
the `c2` modifier.

### Value Options
These are special modifiers whose values can be specified through their use in a
[configuration string](#configs). Concrete values are specified as `-` separated
values after the modifier's name in a configuration string. These values will be
indexed by the modifier through syntax similar to Python format strings.

This is best understood via an example:
```yaml
modifiers:
  env_var:
    type: EnvVar
    var: "FOO{0}"
    val: "{1}"

[...]

configs:
  - "openjdk11|env_var-42-43"
```
specifies to run the `openjdk11` [`runtime`](#runtimes) with the environment
variable `FOO42` set to `43`. Note that value options are not limited only to
environment variables, and can be used for all modifier `type`s.

## `runtimes`
A YAML dictionary of runtime definitions that are to be used with [config strings](#configs).
Each runtime requires a `type` key with other keys being specific to that
`type`. For more information regarding the different `type`s of runtimes,
please refer to [this page](./runtime.md).

## `suites`
A YAML dictionary of benchmark suite definitions that are to be used as keys of `benchmarks`.
Each benchmark suite requires a `type` key with other keys being specific to that
`type`. For more information regarding the different `type`s of benchmark suites,
please refer to [this page](./suite.md).
