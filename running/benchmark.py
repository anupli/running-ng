import logging
import subprocess
import sys
from typing import Any, List, Optional, Tuple, Union, Dict
from running.runtime import Runtime
from running.modifier import JVMArg, EnvVar, Modifier, ProgramArg, JVMClasspath
from running.util import smart_quote, split_quoted
from pathlib import Path
from copy import deepcopy
from running import suite
import os
from enum import Enum


class SubprocessrExit(Enum):
    Normal = 1
    Error = 2
    Timeout = 3
    Dryrun = 4


class Benchmark(object):
    def __init__(self, suite_name: str, bm_name: str, wrapper: Optional[str] = None, **kwargs):
        self.name = bm_name
        self.suite_name = suite_name
        self.env_args: Dict[str, str]
        self.env_args = {}
        self.wrapper: List[str]
        if wrapper is not None:
            self.wrapper = split_quoted(wrapper)
        else:
            self.wrapper = []

    def get_env_str(self) -> str:
        return " ".join([
            "{}={}".format(k, smart_quote(v))
            for (k, v) in self.env_args.items()
        ])

    def get_full_args(self, _executable: Union[str, Path]) -> List[Union[str, Path]]:
        # makes a copy because the subclass might change the list
        # also to type check https://mypy.readthedocs.io/en/stable/common_issues.html#variance
        return list(self.wrapper)

    def attach_modifiers(self, _modifiers: List[Modifier]) -> Any:
        raise NotImplementedError

    def to_string(self, executable: Union[str, Path]) -> str:
        return "{} {}".format(
            self.get_env_str(),
            " ".join([
                smart_quote(x)
                for x in self.get_full_args(executable)
            ])
        )

    def run(self, runtime: Runtime, timeout: int = None, cwd: Path = None) -> Tuple[str, SubprocessrExit]:
        if suite.is_dry_run():
            print(
                self.to_string(runtime.get_executable()),
                file=sys.stderr
            )
            return "", SubprocessrExit.Dryrun
        else:
            cmd = self.get_full_args(runtime.get_executable())
            env_args = os.environ.copy()
            env_args.update(self.env_args)
            try:
                p = subprocess.run(
                    cmd,
                    env=env_args,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    timeout=timeout,
                    cwd=cwd
                )
                return p.stdout.decode("utf-8"), SubprocessrExit.Normal
            except subprocess.CalledProcessError as e:
                return e.stdout.decode("utf-8"), SubprocessrExit.Error
            except subprocess.TimeoutExpired as e:
                return e.stdout.decode("utf-8"), SubprocessrExit.Timeout


class BinaryBenchmark(Benchmark):
    def __init__(self, program: Path, program_args: List[Union[str, Path]], **kwargs):
        super().__init__(**kwargs)
        self.program = program
        self.program_args = program_args
        assert program.exists()

    def __str__(self) -> str:
        return self.to_string("")

    def attach_modifiers(self, modifiers: List[Modifier]) -> 'BinaryBenchmark':
        bp = deepcopy(self)
        for m in modifiers:
            if self.suite_name in m.excludes:
                if self.name in m.excludes[self.suite_name]:
                    continue
            elif type(m) == EnvVar:
                bp.env_args[m.var] = m.val
            elif type(m) == ProgramArg:
                bp.program_args.extend(m.val)
            elif type(m) == JVMArg:
                logging.warning("JVMArg not respected by BinaryBenchmark")
                pass
            else:
                raise ValueError()
        return bp

    def get_full_args(self, _executable: Union[str, Path]) -> List[Union[str, Path]]:
        cmd = super().get_full_args(_executable)
        cmd.append(self.program)
        cmd.extend(self.program_args)
        return cmd


class JavaBenchmark(Benchmark):
    def __init__(self, jvm_args: List[str], program_args: List[str], cp: List[str], **kwargs):
        super().__init__(**kwargs)
        self.jvm_args = jvm_args
        self.program_args = program_args
        self.cp = cp

    def get_classpath_args(self) -> List[str]:
        return ["-cp", ":".join(self.cp)] if self.cp else []

    def __str__(self) -> str:
        return self.to_string("java")

    def attach_modifiers(self, modifiers: List[Modifier]) -> 'JavaBenchmark':
        jp = deepcopy(self)
        for m in modifiers:
            if self.suite_name in m.excludes:
                if self.name in m.excludes[self.suite_name]:
                    continue
            if type(m) == JVMArg:
                jp.jvm_args.extend(m.val)
            elif type(m) == EnvVar:
                jp.env_args[m.var] = m.val
            elif type(m) == ProgramArg:
                jp.program_args.extend(m.val)
            elif type(m) == JVMClasspath:
                jp.cp.extend(m.val)
            else:
                raise ValueError()
        return jp

    def get_full_args(self, executable: Union[str, Path]) -> List[Union[str, Path]]:
        cmd = super().get_full_args(executable)
        cmd.append(executable)
        cmd.extend(self.jvm_args)
        cmd.extend(self.get_classpath_args())
        cmd.extend(self.program_args)
        return cmd
