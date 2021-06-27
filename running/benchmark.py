from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from running.jvm import JVM
from running.modifier import JVMArg, EnvVar, Modifier, ProgramArg, JVMClasspath
from copy import deepcopy
import subprocess
import sys
import logging

DRY_RUN = False


class JavaBenchmarkSuite(object):
    def __init__(self, **kwargs):
        self.name = kwargs["name"]

    @staticmethod
    def from_config(name: str, config: Dict[str, str]) -> Any:
        return eval(config["type"])(name=name, **config)

    def __str__(self) -> str:
        return "Benchmark Suite {}".format(self.name)

    def get_benchmark(self, bm_name: str) -> 'JavaProgram':
        raise NotImplementedError()

    def get_minheap(self, bm_name: str) -> int:
        raise NotImplementedError()

    def get_timeout(self, bm_name: str) -> int:
        raise NotImplementedError()


class DaCapo(JavaBenchmarkSuite):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.release = kwargs["release"]
        if self.release not in ["2006", "9.12", "evaluation"]:
            logging.info(
                "DaCapo release {} not recongized".format(self.release))
        self.path: Path
        self.path = Path(kwargs["path"])
        if not self.path.exists():
            logging.info("DaCapo jar {} not found".format(self.path))
        self.minheap = kwargs.get("minheap", {})
        try:
            self.timing_iteration = int(kwargs.get("timing_iteration"))
        except TypeError:
            logging.warning(
                "Timing iteration not set for DaCapo {}, use default value 3".format(self.path))
            self.timing_iteration = 3
        self.callback = kwargs.get("callback")

    def __str__(self) -> str:
        return "{} DaCapo {} {}".format(super().__str__(), self.release, self.path)

    def get_benchmark(self, bm_name: str) -> 'JavaProgram':
        if self.callback:
            cp = [str(self.path)]
            jvm_args = []
            progam_args = ["Harness", "-c", self.callback]
        else:
            cp = []
            jvm_args = ["-jar", str(self.path)]
            progam_args = []
        progam_args.extend(["-n", str(self.timing_iteration), bm_name])
        return JavaProgram(self.name, bm_name, jvm_args, progam_args, cp)

    def get_minheap(self, bm_name: str) -> int:
        if bm_name not in self.minheap:
            logging.warn("Minheap for {} of {} not set".format(bm_name, self))
            return 4096
        return self.minheap[bm_name]

    def get_timeout(self, bm_name: str) -> int:
        # FIXME
        return 120


class JavaProgram(object):
    def __init__(self, suite_name: str, bm_name: str, jvm_args: List[str], progam_args: List[str], cp: List[str], env_args: Optional[Dict[str, str]] = None):
        self.name = "{}-{}".format(suite_name, bm_name)
        self.bm_name = bm_name
        self.jvm_args = jvm_args
        self.progam_args = progam_args
        self.cp = cp
        if env_args is None:
            self.env_args = {}
        else:
            self.env_args = env_args

    def get_classpath_args(self) -> List[str]:
        return ["-cp", ":".join(self.cp) if self.cp else ""]

    def __str__(self) -> str:
        return self.to_string("java")

    def attach_modifiers(self, modifiers: List[Modifier]) -> 'JavaProgram':
        jp = deepcopy(self)
        for m in modifiers:
            if type(m) == JVMArg:
                jp.jvm_args.extend(m.val)
            elif type(m) == EnvVar:
                jp.env_args[m.var] = m.val
            elif type(m) == ProgramArg:
                jp.progam_args.extend(m.val)
            elif type(m) == JVMClasspath:
                jp.cp.extend(m.val)
            else:
                raise ValueError()
        return jp

    def get_full_args(self, executable: Union[str, Path]) -> List[Union[str, Path]]:
        cmd = [executable]
        cmd.extend(self.jvm_args)
        cmd.extend(self.get_classpath_args())
        cmd.extend(self.progam_args)
        return cmd

    def get_env_str(self) -> str:
        return " ".join(["{}={}".format(k, v) for (k, v) in self.env_args.items()])

    def to_string(self, executable: Union[str, Path]) -> str:
        return "{} {}".format(
            self.get_env_str(),
            " ".join([str(x) for x in self.get_full_args(executable)])
        )

    def run(self, jvm: JVM, timeout: int = None) -> str:
        cmd = self.get_full_args(jvm.get_executable())
        if DRY_RUN:
            print(
                self.to_string(jvm.get_executable()),
                file=sys.stderr
            )
            return ""
        else:
            try:
                p = subprocess.run(
                    cmd,
                    env=self.env_args,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    timeout=timeout
                )
                return p.stdout.decode("utf-8")
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
                return e.stdout.decode("utf-8")
