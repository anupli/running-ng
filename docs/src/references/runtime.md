# Runtime

## `JikesRVM`

## `NativeExecutable` (preview ⚠️)
A `NativeExecutable` type specifies [`runbms`](../commands/runbms.md) to
directly run the benchmarks on native hardware. This is supposed to be used in
tandem with
[`BinaryBenchmarkSuite`](./suite.md#BinaryBenchmarkSuite).

## `OpenJDK`

## `D8` (preview ⚠️)
### Keys
`executable`: path to the `d8` executable.

## `SpiderMonkey` (preview ⚠️)
### Keys
`executable`: path to the `js` executable.

## `JavaScriptCore` (preview ⚠️)
### Keys
`executable`: path to the `jsc` executable.

## `JuliaMMTK` (preview ⚠️)
### Keys
`executable`: path to the `julia` executable.

## `JuliaStock` (preview ⚠️)
Julia with the stock GC. It does not allow setting a heap size, and will not throw OOM unless killed by the operating system.
### Keys
`executable`: path to the `julia` executable.
