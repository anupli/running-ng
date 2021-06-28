from typing import Any, Dict
from running.util import register
import copy


class Modifier(object):
    CLS_MAPPING: Dict[str, Any]
    CLS_MAPPING = {}

    def __init__(self, value_opts=None, **kwargs):
        self.name = kwargs["name"]
        if value_opts is None:
            self.value_opts = []
        if "-" in self.name:
            raise ValueError(
                "Modifier {} has - in its name. - is reserved for value modifiers.".format(self.name))
        self.__original_kwargs = kwargs
        self._kwargs = copy.deepcopy(kwargs)
        if not value_opts:
            return
        # Expand value opts
        for k, v in kwargs.items():
            try:
                self._kwargs[k] = v.format(*value_opts)
            except IndexError:
                pass

    @staticmethod
    def from_config(name: str, config: Dict[str, str]) -> Any:
        return Modifier.CLS_MAPPING[config["type"]](name=name, **config)

    def apply_value_opts(self, value_opts):
        return type(self)(value_opts, **self.__original_kwargs)

    def __str__(self) -> str:
        return "Modifier {}".format(self.name)


@register(Modifier)
class JVMArg(Modifier):
    def __init__(self, value_opts=None, **kwargs):
        super().__init__(value_opts, **kwargs)
        self.val = self._kwargs["val"].split()

    def __str__(self) -> str:
        return "{} JVMArg {}".format(super().__str__(), self.val)


@register(Modifier)
class JVMClasspath(Modifier):
    def __init__(self, value_opts=None, **kwargs):
        super().__init__(value_opts, **kwargs)
        self.val = self._kwargs["val"].split()

    def __str__(self) -> str:
        return "{} JVMClasspath {}".format(super().__str__(), self.val)


@register(Modifier)
class EnvVar(Modifier):
    def __init__(self, value_opts=None, **kwargs):
        super().__init__(value_opts, **kwargs)
        self.var = self._kwargs["val"].split("=")[0]
        self.val = self._kwargs["val"][len(self.var)+1:]  # skip '='

    def __str__(self) -> str:
        return "{} EnvVar {}={}".format(super().__str__(), self.var, self.val)


@register(Modifier)
class ProgramArg(Modifier):
    def __init__(self, value_opts=None, **kwargs):
        super().__init__(value_opts, **kwargs)
        self.val = self._kwargs["val"].split()

    def __str__(self) -> str:
        return "{} ProgramArg {}".format(super().__str__(), self.val)
