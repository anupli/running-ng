import subprocess
import sys
from typing import List, Optional, Union, Dict
from running.jvm import JVM
from running.modifier import JVMArg, EnvVar, Modifier, ProgramArg, JVMClasspath
from pathlib import Path
from copy import deepcopy
from running import suite


class JavaBenchmark(object):
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

    def attach_modifiers(self, modifiers: List[Modifier]) -> 'JavaBenchmark':
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

    def run(self, jvm: JVM, timeout: int = None, cwd: Path = None) -> str:
        cmd = self.get_full_args(jvm.get_executable())
        if suite.is_dry_run():
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
                    timeout=timeout,
                    cwd=cwd
                )
                return p.stdout.decode("utf-8")
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
                return e.stdout.decode("utf-8")
