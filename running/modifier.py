from typing import Any, Dict


class Modifier(object):
    def __init__(self, **kwargs):
        self.name = kwargs["name"]

    @staticmethod
    def from_config(name: str, config: Dict[str, str]) -> Any:
        return eval(config["type"])(name=name, **config)

    def __str__(self) -> str:
        return "Modifier {}".format(self.name)


class JVMArg(Modifier):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.val = kwargs["val"].split()

    def __str__(self) -> str:
        return "{} JVMArg {}".format(super().__str__(), self.val)


class JVMClasspath(Modifier):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.val = kwargs["val"].split()

    def __str__(self) -> str:
        return "{} JVMClasspath {}".format(super().__str__(), self.val)


class EnvVar(Modifier):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.var = kwargs["val"].split("=")[0]
        self.val = kwargs["val"][len(self.var)+1:]  # skip '='

    def __str__(self) -> str:
        return "{} EnvVar {}={}".format(super().__str__(), self.var, self.val)


class ProgramArg(Modifier):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.val = kwargs["val"].split()

    def __str__(self) -> str:
        return "{} ProgramArg {}".format(super().__str__(), self.val)
