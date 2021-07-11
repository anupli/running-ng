from typing import Any, Dict, Union
from pathlib import Path
import logging
from running.util import register


class Runner(object):
    CLS_MAPPING: Dict[str, Any]
    CLS_MAPPING = {}

    def __init__(self, name: str, **kwargs):
        self.name = name

    @staticmethod
    def from_config(name: str, config: Dict[str, str]) -> Any:
        return Runner.CLS_MAPPING[config["type"]](name=name, **config)

    def get_executable(self) -> Union[str, Path]:
        raise NotImplementedError


@register(Runner)
class NativeExecutable(Runner):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def get_executable(self) -> Union[str, Path]:
        return ""


class JVM(Runner):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def get_executable(self) -> Path:
        raise NotImplementedError

    def __str__(self):
        return "JVM {}".format(self.name)


@register(Runner)
class OpenJDK(JVM):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.release = kwargs["release"]
        self.home: Path
        self.home = Path(kwargs["home"])
        if not self.home.exists():
            logging.warn("OpenJDK home {} doesn't exist".format(self.home))
        self.executable = self.home / "bin" / "java"
        if not self.executable.exists():
            logging.warn(
                "{} not found in OpenJDK home".format(self.executable))

    def get_executable(self) -> Path:
        return self.executable

    def __str__(self):
        return "{} OpenJDK {} {}".format(super().__str__(), self.release, self.home)


@register(Runner)
class JikesRVM(JVM):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.home: Path
        self.home = Path(kwargs["home"])
        if not self.home.exists():
            logging.warn("JikesRVM home {} doesn't exist".format(self.home))
        self.executable = self.home / "rvm"
        if not self.home.exists():
            logging.warn(
                "{} not found in JikesRVM home".format(self.executable))

    def get_executable(self) -> Path:
        return self.executable

    def __str__(self):
        return "{} JikesRVM {} {}".format(super().__str__(), self.release, self.home)
