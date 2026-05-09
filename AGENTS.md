# AGENTS.md

This file provides guidance to AI coding agents when working with code in this repository.

## Project

`running-ng` is a Python CLI (`running`) for running benchmark workloads (mostly JVM/managed-runtime performance experiments) in a methodologically sound way. It is used by Steve Blackburn's lab at ANU and is built around YAML configuration files that describe suites, runtimes, modifiers, and configs.

## Common commands

See [README.md](README.md) for setup and build instructions. Below are the commands agents need most.

```bash
# tests — CI runs each file separately because they share global state
for f in tests/test_*.py; do uv run pytest "$f"; done
# single test file / single test
uv run pytest tests/test_runbms.py
uv run pytest tests/test_runbms.py::test_spread_0

uv run ty check src/running
uv run ruff check src tests
uv run ruff format --check src tests
```

### Pre-commit workflow

Before committing, run:
```bash
uv run ruff format src tests       # auto-format
uv run ruff check --fix src tests  # lint + auto-fix
uv run ty check src/running        # type check
for f in tests/test_*.py; do uv run pytest "$f"; done  # tests
```

The `running` CLI has subcommands: `runbms`, `minheap`, `fillin`, `preproc` (see [src/running/__main__.py](src/running/__main__.py)). Run from a checkout with `uv run running <subcommand>`.

## Architecture

The code splits into a **core** (data model for experiments) and **commands** (user-facing entry points that consume the core).

### Core abstractions

Each of these is a base class with a `CLS_MAPPING` registry populated by the `@register(ParentClass)` decorator from [src/running/util.py](src/running/util.py). To add a new suite/runtime/modifier/plugin type, define a subclass and decorate it — no other wiring is needed, but the module containing the subclass must be imported during startup so the decorator runs (see the bottom of [src/running/plugin/runbms/__init__.py](src/running/plugin/runbms/__init__.py) for the explicit-import pattern, including the optional-dependency fallback for the Zulip plugin).

- [BenchmarkSuite](src/running/suite.py) — DaCapo, SPECjvm98, SPECjbb2015, Octane, JuliaGCBenchmarks, BinaryBenchmarkSuite, etc. Owns `get_benchmark`, `get_minheap`, `is_passed`.
- [Runtime](src/running/runtime.py) — OpenJDK, JikesRVM, JavaScriptCore, D8, SpiderMonkey, NativeExecutable, JuliaMMTk, JuliaStock, etc. Owns `get_executable`, `get_heapsize_modifiers`, `is_oom`.
- [Modifier](src/running/modifier.py) — JVMArg, JVMClasspath, JSArg, EnvVar, ModifierSet, NoImplicitHeapsizeModifier, etc. Modifiers can take `value_opts` (the `-foo-bar` suffix on a config string is `format()`-substituted into the modifier's string fields) and have `includes`/`excludes` filters per (suite, benchmark).
- [Benchmark](src/running/benchmark.py) — JavaBenchmark, BinaryBenchmark, JavaScriptBenchmark, JuliaBenchmark. Knows how to assemble and run a subprocess command line with a wrapper, companion process, env vars, and a timeout.
- [RunbmsPlugin](src/running/plugin/runbms/__init__.py) — lifecycle hooks (`start_hfac`/`end_hfac`, `start_benchmark`/`end_benchmark`, `start_invocation`/`end_invocation`, `start_config`/`end_config`) that fire from `runbms`. Built-ins: `CopyFile`, `Zulip`.

### Configuration system

[Configuration](src/running/config.py) is a layered dictionary loaded from YAML. Two mechanisms compose configs:

- `includes:` — list of files merged via `Configuration.combine` (lists concatenate, dicts update, scalar collisions raise `TypeError`). Resolved recursively, relative to the including file. `$VAR` env vars in include paths are expanded — most importantly `$RUNNING_NG_PACKAGE_DATA`, which `__main__.py` sets to point at [src/running/config/](src/running/config/) so user configs can include base files (e.g., `$RUNNING_NG_PACKAGE_DATA/base/runbms.yml`).
- `overrides:` — dotted-path selectors (`"a.b.0.c"`) applied after includes. Numeric components index into lists.

After loading, `resolve_class()` instantiates the actual `BenchmarkSuite`/`Runtime`/`Modifier` objects from their dict form via `KEY_CLASS_MAPPING`, then resolves `benchmarks: { suite_name: [bm, ...] }` against those suites.

### Config string syntax

A config like `build1|ms|s|c2|mmtk_gc-SemiSpace|tph|probes_cp|probes` is parsed by `parse_config_str` ([src/running/util.py](src/running/util.py)): the first segment names a runtime; the rest name modifiers. A modifier name may carry `-`-separated `value_opts` (e.g. `mmtk_gc-SemiSpace`) which are substituted into the modifier's string fields with `str.format`. `ModifierSet` modifiers expand into multiple modifiers via `flatten`.

### `runbms` (the main command)

[src/running/command/runbms.py](src/running/command/runbms.py) is the heart of the tool. The CLI shape is `running runbms LOG_DIR CONFIG N [n ...]`, where `N` controls heap-fraction sampling: with `N` and no explicit `n`s, `runbms` uses `fillin` ([src/running/command/fillin.py](src/running/command/fillin.py)) to choose which fractions of the heap-size space to explore in a logarithmic, ends-then-middles order, so partial runs still cover the space sensibly. The `spread` function (in `runbms.py`) biases sampling toward smaller heap sizes (where small changes have outsized effect on GC). For each (hfac, size, benchmark, invocation, config), runbms invokes the benchmark via the runtime, applies modifiers, fires plugin hooks, and writes a per-invocation gzipped log into `LOG_DIR/<run_id>/`. It also persists the flattened config and CLI args alongside the logs for reproducibility.

Module-level globals (`configuration`, `minheap_multiplier`, `plugins`, `resume`, etc.) hold runbms state — this is why CI runs each test file in a separate `pytest` invocation rather than discovering the whole `tests/` directory at once.

### Other commands

- `minheap` ([command/minheap.py](src/running/command/minheap.py)) — binary-search the minimum heap size at which each benchmark passes, given a runtime/modifier config.
- `fillin` ([command/fillin.py](src/running/command/fillin.py)) — exposes the `fillin` sampler as a standalone CLI that pipes fractions into an external program.
- `preproc` ([command/log_preprocessor.py](src/running/command/log_preprocessor.py)) — post-process logs (e.g., MMTk Statistics blocks) into structured form.

## Conventions

- `ruff` formats and lints `src` and `tests`; CI fails on diff or lint errors. Run `uv run ruff format src tests && uv run ruff check --fix src tests` before committing.
- `ty check src/running` must pass (type checking).
- Supported Python versions: 3.10 through 3.14 (matrix in CI; covers Ubuntu 22.04–26.04).
- Only `pyyaml` is a hard dependency; `zulip` is optional and gated behind a try/except import in [plugin/runbms/__init__.py](src/running/plugin/runbms/__init__.py) — preserve that pattern for any other optional integration.
- Base YAML configs shipped with the package live under [src/running/config/base/](src/running/config/base/) and are exposed to user configs via `$RUNNING_NG_PACKAGE_DATA`. Updating these affects every user who `includes:` them.
- User-facing docs are an mdBook in [docs/](docs/) (`book.toml` + `docs/src/`); update them when changing CLI flags or YAML schema. The mdBook is built and deployed by [.github/workflows/mdbook.yml](.github/workflows/mdbook.yml).
