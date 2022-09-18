# `running-ng`
`running-ng` is a collection of scripts that help people run workloads in a methodologically sound settings.

## Installation
`pip3 install running-ng`

## Development setup
```console
virtualenv env
source env/bin/activate
pip install -U pip setuptools build[virtualenv]
```

To make a distribution archives, run `python -m build` within the virtual environment.
To run an editable build in the virtual environment, run `pip install -e .`.
To install to user `site-packages`, run `pip install dist/running_ng-<VERSION>-py3-none-any.whl` outside the virtual environment.

There are two [extras](https://peps.python.org/pep-0508/#extras) available.
- `zulip`: dependencies for the `Zulip` `runbms` plugin.
- `tests`: dependencies for running tests.

## Documentation
Please refer to [this site](https://anupli.github.io/running-ng/) for up-to-date documentations.

## License
This project is licensed under the Apache License, Version 2.0.
