# `running-ng`
`running-ng` is a collection of scripts that help people run workloads in a methodologically sound settings.

## Installation
```bash
pip3 install running-ng
# or, to install as an isolated tool:
uv tool install running-ng
pipx install running-ng
```

There is one [extra](https://peps.python.org/pep-0508/#extras) available.
- `zulip`: dependencies for the `Zulip` `runbms` plugin, useful for users.

Dev dependencies (`pytest`, `ruff`, `ty`) are in the `dev` [dependency group](https://peps.python.org/pep-0735/) — see **Development setup** below.

To install with the `zulip` extra, append `[zulip]` to the package name, e.g. `uv tool install 'running-ng[zulip]'` or `pipx install 'running-ng[zulip]'`.

## Development setup
This project uses [`uv`](https://docs.astral.sh/uv/). Install `uv` first, then:
```bash
uv sync --group dev --extra zulip
```
This creates a `.venv/` and installs all runtime, optional (`zulip`), and dev (`pytest`, `ruff`, `ty`, `types-PyYAML`) dependencies pinned in `uv.lock`.

Run any tool inside the project environment with `uv run`, e.g. `uv run running <subcommand>`, `uv run pytest`, `uv run ruff check src tests`, `uv run ty check src/running`.

- To build distribution archives, run `uv build`.
- To install to user `site-packages`, run `pip install dist/running_ng-<VERSION>-py3-none-any.whl` (or `uv tool install dist/running_ng-<VERSION>-py3-none-any.whl`).
- To upload to PyPI, run `uv publish dist/*<VERSION>*` (you can also still use `twine upload --repository running-ng dist/*<VERSION>*`).

## Documentation
Please refer to [this site](https://anupli.github.io/running-ng/) for up-to-date documentations.

## License
This project is licensed under the Apache License, Version 2.0.
