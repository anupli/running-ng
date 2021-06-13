from typing import Any, Dict
from pathlib import Path


class JVM(object):
    def __init__(self, **kwargs):
        self.name = kwargs["name"]

    @staticmethod
    def from_config(name: str, config: Dict[str, str]) -> Any:
        return eval(config["type"])(name=name, **config)

    def __str__(self):
        return "JVM {}".format(self.name)


class OpenJDK(JVM):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.release = kwargs["release"]
        self.home: Path
        self.home = Path(kwargs["home"])
        assert self.home.exists()
        self.executable = self.home / "bin" / "java"
        assert self.executable.exists()

    def __str__(self):
        return "{} OpenJDK {} {}".format(super().__str__(), self.release, self.home)


class JikesRVM(JVM):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.home: Path
        self.home = Path(kwargs["home"])
        assert self.home.exists()
        self.executable = self.home / "rvm"
        assert self.executable.exists()

    def __str__(self):
        return "{} JikesRVM {} {}".format(super().__str__(), self.release, self.home)
