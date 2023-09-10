import logging
import subprocess
import sys
from time import sleep
from typing import Callable, Sequence, TypeVar, List, Optional, Tuple, Union, Dict
from running.runtime import D8, JavaScriptCore, Runtime, DummyRuntime, SpiderMonkey
from running.modifier import *
from running.util import smart_quote, split_quoted
from pathlib import Path
from copy import deepcopy
from running import suite
import os
from enum import Enum

COMPANION_WAIT_START = 2.0


class SubprocessrExit(Enum):
    Normal = 1
    Error = 2
    Timeout = 3
    Dryrun = 4


B = TypeVar('B', bound='Benchmark')


class Benchmark(object):
    def __init__(self, suite_name: str, name: str, wrapper: Optional[str] = None, timeout: Optional[int] = None, override_cwd: Optional[Path] = None, companion: Optional[str] = None, runtime_specific_modifiers_strategy: Optional[Callable[[Runtime], Sequence[Modifier]]] = None, **kwargs):
        self.name = name
        self.suite_name = suite_name
        self.env_args: Dict[str, str]
        self.env_args = {}
        self.wrapper: List[str]
        if wrapper is not None:
            self.wrapper = split_quoted(wrapper)
        else:
            self.wrapper = []
        if companion is not None:
            self.companion = split_quoted(companion)
        else:
            self.companion = []
        self.timeout = timeout
        # ignore the current working directory provided by commands like runbms or minheap
        # certain benchmarks expect to be invoked from certain directories
        self.override_cwd = override_cwd
        self.runtime_specific_modifiers_strategy: Callable[[
            Runtime], Sequence[Modifier]]
        if runtime_specific_modifiers_strategy is not None:
            self.runtime_specific_modifiers_strategy = runtime_specific_modifiers_strategy
        else:
            self.runtime_specific_modifiers_strategy = lambda _runtime: []

    def get_env_str(self) -> str:
        return " ".join([
            "{}={}".format(k, smart_quote(v))
            for (k, v) in self.env_args.items()
        ])

    def get_full_args(self, _runtime: Runtime) -> List[Union[str, Path]]:
        # makes a copy because the subclass might change the list
        # also to type check https://mypy.readthedocs.io/en/stable/common_issues.html#variance
        return list(self.wrapper)

    def get_runtime_specific_modifiers(self, runtime: Runtime) -> Sequence[Modifier]:
        return self.runtime_specific_modifiers_strategy(runtime)

    def attach_modifiers(self: B, modifiers: Sequence[Modifier]) -> B:
        b = deepcopy(self)
        for m in modifiers:
            if not m.should_attach(self.suite_name, self.name):
                continue
            elif type(m) == Wrapper:
                b.wrapper.extend(m.val)
            elif type(m) == Companion:
                b.companion.extend(m.val)
            elif type(m) == EnvVar:
                b.env_args[m.var] = m.val
            elif type(m) == ModifierSet:
                logging.warning("ModifierSet should have been flattened")
        return b

    def to_string(self, runtime: Runtime) -> str:
        return "{} {}".format(
            self.get_env_str(),
            " ".join([
                smart_quote(os.path.expandvars(x))
                for x in self.get_full_args(runtime)
            ])
        )

    def run(self, runtime: Runtime, cwd: Optional[Path] = None) -> Tuple[bytes, bytes, SubprocessrExit]:
        if suite.is_dry_run():
            print(
                self.to_string(runtime),
                file=sys.stderr
            )
            return b"", b"", SubprocessrExit.Dryrun
        else:
            cmd = self.get_full_args(runtime)
            cmd = [os.path.expandvars(x) for x in cmd]
            env_args = os.environ.copy()
            env_args.update(self.env_args)
            companion_out = b""
            stdout: Optional[bytes]
            if self.companion:
                companion_p = subprocess.Popen(
                    self.companion, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                sleep(COMPANION_WAIT_START)
            try:
                p = subprocess.run(
                    cmd,
                    env=env_args,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    timeout=self.timeout,
                    cwd=self.override_cwd if self.override_cwd else cwd
                )
                subprocess_exit = SubprocessrExit.Normal
                stdout = p.stdout
            except subprocess.CalledProcessError as e:
                subprocess_exit = SubprocessrExit.Error
                stdout = e.stdout
            except subprocess.TimeoutExpired as e:
                subprocess_exit = SubprocessrExit.Timeout
                stdout = e.stdout
            finally:
                if self.companion:
                    try:
                        companion_stdout, _ = companion_p.communicate(
                            timeout=10)
                        companion_out += companion_stdout
                    except subprocess.TimeoutExpired:
                        logging.warning(
                            "Companion program not exited after 10 seconds timeout. Trying to kill ...")
                        try:
                            companion_p.kill()
                        except PermissionError:
                            logging.warning("Failed to kill.")
                        companion_stdout, _ = companion_p.communicate()
                        companion_out += companion_stdout

            return stdout if stdout else b"", companion_out, subprocess_exit


class BinaryBenchmark(Benchmark):
    def __init__(self, program: Path, program_args: List[Union[str, Path]], **kwargs):
        super().__init__(**kwargs)
        self.program = program
        self.program_args = program_args
        assert program.exists()

    def __str__(self) -> str:
        return self.to_string(DummyRuntime(""))

    def attach_modifiers(self, modifiers: Sequence[Modifier]) -> 'BinaryBenchmark':
        bb = super().attach_modifiers(modifiers)
        for m in modifiers:
            if not m.should_attach(self.suite_name, self.name):
                continue
            elif type(m) == ProgramArg:
                bb.program_args.extend(m.val)
            elif type(m) == JVMArg:
                logging.warning("JVMArg not respected by BinaryBenchmark")
            elif isinstance(m, JVMClasspathAppend) or type(m) == JVMClasspathPrepend:
                logging.warning(
                    "JVMClasspath not respected by BinaryBenchmark")
            elif type(m) == JSArg:
                logging.warning(
                    "JSArg not respected by BinaryBenchmark")
        return bb

    def get_full_args(self, _runtime: Runtime) -> List[Union[str, Path]]:
        cmd = super().get_full_args(_runtime)
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
        return self.to_string(DummyRuntime("java"))

    def attach_modifiers(self, modifiers: Sequence[Modifier]) -> 'JavaBenchmark':
        jb = super().attach_modifiers(modifiers)
        for m in modifiers:
            if not m.should_attach(self.suite_name, self.name):
                continue
            if type(m) == JVMArg:
                jb.jvm_args.extend(m.val)
            elif type(m) == ProgramArg:
                jb.program_args.extend(m.val)
            elif isinstance(m, JVMClasspathAppend):
                jb.cp.extend(m.val)
            elif type(m) == JVMClasspathPrepend:
                jb.cp = m.val + jb.cp
            elif type(m) == JSArg:
                logging.warning(
                    "JSArg not respected by JavaBenchmark")
        return jb

    def get_full_args(self, runtime: Runtime) -> List[Union[str, Path]]:
        cmd = super().get_full_args(runtime)
        cmd.append(runtime.get_executable())
        cmd.extend(self.jvm_args)
        cmd.extend(self.get_classpath_args())
        cmd.extend(self.program_args)
        return cmd


class JavaScriptBenchmark(Benchmark):
    def __init__(self, js_args: List[str], program: str, program_args: List[str], **kwargs):
        super().__init__(**kwargs)
        self.js_args = js_args
        self.program = program
        self.program_args = program_args

    def __str__(self) -> str:
        return self.to_string(DummyRuntime("js"))

    def attach_modifiers(self, modifiers: Sequence[Modifier]) -> 'JavaScriptBenchmark':
        jb = super().attach_modifiers(modifiers)
        for m in modifiers:
            if not m.should_attach(self.suite_name, self.name):
                continue
            if type(m) == ProgramArg:
                jb.program_args.extend(m.val)
            elif type(m) == JVMArg:
                logging.warning("JVMArg not respected by JavaScriptBenchmark")
            elif isinstance(m, JVMClasspathAppend) or type(m) == JVMClasspathPrepend:
                logging.warning(
                    "JVMClasspath not respected by JavaScriptBenchmark")
            elif type(m) == JSArg:
                jb.js_args.extend(m.val)
        return jb

    def get_full_args(self, runtime: Runtime) -> List[Union[str, Path]]:
        cmd = super().get_full_args(runtime)
        cmd.append(runtime.get_executable())
        cmd.extend(self.js_args)
        cmd.append(self.program)
        if isinstance(runtime, D8):
            cmd.append("--")
        elif isinstance(runtime, JavaScriptCore):
            cmd.append("--")
        elif isinstance(runtime, SpiderMonkey):
            pass
        else:
            raise TypeError("{} is of type {}, and not a valid runtime for JavaScriptBenchmark".format(
                runtime, type(runtime)))
        cmd.extend(self.program_args)
        return cmd


class JuliaBenchmark(Benchmark):
    def __init__(self, julia_args: List[str], suite_path: Path, program_args: List[str], **kwargs):
        super().__init__(**kwargs)
        self.julia_args = julia_args
        self.suite_path = suite_path
        self.program_args = program_args

    def __str__(self) -> str:
        return self.to_string(DummyRuntime("julia"))

    def attach_modifiers(self, modifiers: Sequence[Modifier]) -> 'JuliaBenchmark':
        jb = super().attach_modifiers(modifiers)
        for m in modifiers:
            if type(m) == JuliaArg:
                jb.julia_args.extend(m.val)
            elif type(m) == ProgramArg:
                jb.program_args.extend(m.val)
        return jb

    def get_full_args(self, runtime: Runtime) -> List[Union[str, Path]]:
        cmd = super().get_full_args(runtime)
        cmd.append(runtime.get_executable())
        cmd.extend(self.julia_args)
        cmd.append("--project={}".format(self.suite_path))
        cmd.append(str(self.suite_path / "run_benchmarks.jl"))
        cmd.extend(self.name.split("/"))
        cmd.extend(["-n", "1"])  # one run
        cmd.extend(self.program_args)
        return cmd
