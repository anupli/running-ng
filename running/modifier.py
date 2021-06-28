from typing import Any, Dict
from running.util import register


class Modifier(object):
    CLS_MAPPING: Dict[str, Any]
    CLS_MAPPING = {}

    def __init__(self, **kwargs):
        self.name = kwargs["name"]
        if "-" in self.name:
            raise ValueError(
                "Modifier {} has - in its name. - is reserved for value modifiers.".format(self.name))

    @staticmethod
    def from_config(name: str, config: Dict[str, str]) -> Any:
        return Modifier.CLS_MAPPING[config["type"]](name=name, **config)

    def __str__(self) -> str:
        return "Modifier {}".format(self.name)


@register(Modifier)
class JVMArg(Modifier):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.val = kwargs["val"].split()

    def __str__(self) -> str:
        return "{} JVMArg {}".format(super().__str__(), self.val)


@register(Modifier)
class JVMClasspath(Modifier):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.val = kwargs["val"].split()

    def __str__(self) -> str:
        return "{} JVMClasspath {}".format(super().__str__(), self.val)


@register(Modifier)
class EnvVar(Modifier):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.var = kwargs["val"].split("=")[0]
        self.val = kwargs["val"][len(self.var)+1:]  # skip '='

    def __str__(self) -> str:
        return "{} EnvVar {}={}".format(super().__str__(), self.var, self.val)


@register(Modifier)
class ProgramArg(Modifier):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.val = kwargs["val"].split()

    def __str__(self) -> str:
        return "{} ProgramArg {}".format(super().__str__(), self.val)
