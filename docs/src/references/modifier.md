# Modifier

## `EnvVar`
### Keys
`var`: name of the variable.

`val`: value of the variable.

### Description
Set an environment variable. Might override an environment variable inherited from the parent process.

## `JVMArg`
`JavaBenchmarkSuite` specific.
### Keys
`val`: a single string with [shell-like syntax](https://docs.python.org/3/library/shlex.html#shlex.split).
Multiple arguments are space separated.

### Description
Specify arguments to a JVM, as opposed to the runtime.

## `JVMClasspath`
`JavaBenchmarkSuite` specific.
### Keys
`val`: a single string with [shell-like syntax](https://docs.python.org/3/library/shlex.html#shlex.split).
Multiple classpaths are space separated.

### Description
Specify Java Classpaths.

## `ProgramArg`
### Keys
`val`: a single string with [shell-like syntax](https://docs.python.org/3/library/shlex.html#shlex.split).
Multiple arguments are space separated.

### Description
Specify arguments to a program, as opposed to the runtime.

## `ModifierSet` (preview ⚠️)
### Keys
`val`: `|` separated values, with possible value options. See [here](./index.md#value-options) for details.

### Description
Specify a set of modifiers, including other `ModifierSet`s.
That is, you can use `ModifierSet` recursively.
