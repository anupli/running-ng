from pathlib import Path
from typing import Any, Dict, List, Optional
from running.modifier import JVMArg, EnvVar, Modifier, ProgramArg
from copy import deepcopy
import subprocess

DRY_RUN = False


class JavaBenchmarkSuite(object):
    def __init__(self, **kwargs):
        self.name = kwargs["name"]

    @staticmethod
    def from_config(name: str, config: Dict[str, str]) -> Any:
        return eval(config["type"])(name=name, **config)

    def __str__(self) -> str:
        return "Benchmark Suite {}".format(self.name)

    def get_benchmark(self, name) -> 'JavaProgram':
        raise NotImplementedError()


class DaCapo(JavaBenchmarkSuite):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.release = kwargs["release"]
        assert self.release in ["2006", "9.12", "evaluation"]
        self.path: Path
        self.path = Path(kwargs["path"])
        assert self.path.exists()

    def __str__(self) -> str:
        return "{} DaCapo {} {}".format(super().__str__(), self.release, self.path)

    def get_benchmark(self, name) -> 'JavaProgram':
        args = ["-jar", str(self.path), name]
        return JavaProgram("{} {}".format(self.name, name), args)


class JavaProgram(object):
    def __init__(self, name: str, args: List[str], env_args: Optional[Dict[str, str]] = None):
        self.name = name
        self.args = args
        if env_args is None:
            self.env_args = {}
        else:
            self.env_args = env_args

    def to_string(self, executable):
        return "{} {} {}".format(
            " ".join(["{}={}".format(k, v) for (k, v) in self.env_args.items()]),
            executable,
            " ".join(self.args)
        )

    def __str__(self) -> str:
        return self.to_string("java")

    def attach_modifiers(self, modifiers: List[Modifier]) -> 'JavaProgram':
        jp = deepcopy(self)
        for m in modifiers:
            if type(m) == JVMArg:
                jp.args = m.val + jp.args
            elif type(m) == EnvVar:
                jp.env_args[m.var] = m.val
            elif type(m) == ProgramArg:
                jp.args.extend(m.val)
            else:
                raise ValueError()
        return jp

    def run(self, jvm, timeout: int = None) -> str:
        cmd = [jvm.executable]
        cmd.extend(self.args)
        if DRY_RUN:
            print(self.to_string(jvm.executable))
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
            
