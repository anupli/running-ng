import logging
import subprocess
import sys
from typing import Any, List, Optional, Tuple, Union, Dict
from running.runtime import Runtime
from running.modifier import *
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
    def __init__(self, suite_name: str, name: str, wrapper: Optional[str] = None, timeout: Optional[int] = None, **kwargs):
        self.name = name
        self.suite_name = suite_name
        self.env_args: Dict[str, str]
        self.env_args = {}
        self.wrapper: List[str]
        if wrapper is not None:
            self.wrapper = split_quoted(wrapper)
        else:
            self.wrapper = []
        self.timeout = timeout

    def get_env_str(self) -> str:
        return " ".join([
            "{}={}".format(k, smart_quote(v))
            for (k, v) in self.env_args.items()
        ])

    def get_full_args(self, _executable: Union[str, Path]) -> List[Union[str, Path]]:
        # makes a copy because the subclass might change the list
        # also to type check https://mypy.readthedocs.io/en/stable/common_issues.html#variance
        return list(self.wrapper)

    def attach_modifiers(self, modifiers: List[Modifier]) -> Any:
        b = deepcopy(self)
        for m in modifiers:
            if self.suite_name in m.excludes:
                if self.name in m.excludes[self.suite_name]:
                    continue
            elif type(m) == Wrapper:
                b.wrapper.extend(m.val)
            elif type(m) == EnvVar:
                b.env_args[m.var] = m.val
            elif type(m) == ModifierSet:
                logging.warning("ModifierSet should have been flattened")
        return b

    def to_string(self, executable: Union[str, Path]) -> str:
        return "{} {}".format(
            self.get_env_str(),
            " ".join([
                smart_quote(os.path.expandvars(x))
                for x in self.get_full_args(executable)
            ])
        )

    def run(self, runtime: Runtime, cwd: Path = None) -> Tuple[bytes, SubprocessrExit]:
        if suite.is_dry_run():
            print(
                self.to_string(runtime.get_executable()),
                file=sys.stderr
            )
            return b"", SubprocessrExit.Dryrun
        else:
            cmd = self.get_full_args(runtime.get_executable())
            cmd = [os.path.expandvars(x) for x in cmd]
            env_args = os.environ.copy()
            env_args.update(self.env_args)
            try:
                p = subprocess.run(
                    cmd,
                    env=env_args,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    timeout=self.timeout,
                    cwd=cwd
                )
                return p.stdout, SubprocessrExit.Normal
            except subprocess.CalledProcessError as e:
                return e.stdout, SubprocessrExit.Error
            except subprocess.TimeoutExpired as e:
                return e.stdout, SubprocessrExit.Timeout


class BinaryBenchmark(Benchmark):
    def __init__(self, program: Path, program_args: List[Union[str, Path]], **kwargs):
        super().__init__(**kwargs)
        self.program = program
        self.program_args = program_args
        assert program.exists()

    def __str__(self) -> str:
        return self.to_string("")

    def attach_modifiers(self, modifiers: List[Modifier]) -> 'BinaryBenchmark':
        bb = super().attach_modifiers(modifiers)
        for m in modifiers:
            if self.suite_name in m.excludes:
                if self.name in m.excludes[self.suite_name]:
                    continue
            elif type(m) == ProgramArg:
                bb.program_args.extend(m.val)
            elif type(m) == JVMArg:
                logging.warning("JVMArg not respected by BinaryBenchmark")
            elif type(m) == JVMClasspath:
                logging.warning(
                    "JVMClasspath not respected by BinaryBenchmark")
            elif type(m) == D8Arg:
                logging.warning(
                    "D8Arg not respected by BinaryBenchmark")
        return bb

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
        jb = super().attach_modifiers(modifiers)
        for m in modifiers:
            if self.suite_name in m.excludes:
                if self.name in m.excludes[self.suite_name]:
                    continue
            if type(m) == JVMArg:
                jb.jvm_args.extend(m.val)
            elif type(m) == ProgramArg:
                jb.program_args.extend(m.val)
            elif type(m) == JVMClasspath:
                jb.cp.extend(m.val)
            elif type(m) == D8Arg:
                logging.warning(
                    "D8Arg not respected by JavaBenchmark")
        return jb

    def get_full_args(self, executable: Union[str, Path]) -> List[Union[str, Path]]:
        cmd = super().get_full_args(executable)
        cmd.append(executable)
        cmd.extend(self.jvm_args)
        cmd.extend(self.get_classpath_args())
        cmd.extend(self.program_args)
        return cmd


class D8Benchmark(Benchmark):
    def __init__(self, d8_args: List[str], program: str, program_args: List[str], **kwargs):
        super().__init__(**kwargs)
        self.d8_args = d8_args
        self.program = program
        self.program_args = program_args

    def __str__(self) -> str:
        return self.to_string("d8")

    def attach_modifiers(self, modifiers: List[Modifier]) -> 'D8Benchmark':
        db = super().attach_modifiers(modifiers)
        for m in modifiers:
            if self.suite_name in m.excludes:
                if self.name in m.excludes[self.suite_name]:
                    continue
            if type(m) == ProgramArg:
                db.program_args.extend(m.val)
            elif type(m) == JVMArg:
                logging.warning("JVMArg not respected by D8Benchmark")
            elif type(m) == JVMClasspath:
                logging.warning(
                    "JVMClasspath not respected by D8Benchmark")
            elif type(m) == D8Arg:
                db.d8_args.extend(m.val)
        return db

    def get_full_args(self, executable: Union[str, Path]) -> List[Union[str, Path]]:
        cmd = super().get_full_args(executable)
        cmd.append(executable)
        cmd.extend(self.d8_args)
        cmd.append(self.program)
        cmd.append("--")
        cmd.extend(self.program_args)
        return cmd
