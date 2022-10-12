from typing import Any, Dict, List, TYPE_CHECKING
from running.util import register, smart_quote, split_quoted, parse_modifier_strs
import copy
if TYPE_CHECKING:
    from running.config import Configuration


class Modifier(object):
    CLS_MAPPING: Dict[str, Any]
    CLS_MAPPING = {}

    def __init__(self, value_opts=None, **kwargs):
        self.name = kwargs["name"]
        self.value_opts = value_opts
        if "-" in self.name:
            raise ValueError(
                "Modifier {} has - in its name. - is reserved for value options.".format(self.name))
        self.__original_kwargs = kwargs
        self._kwargs = copy.deepcopy(kwargs)
        self.excludes = kwargs.get("excludes", {})
        if self.value_opts:  # Neither None nor empty
            # Expand value opts
            for k, v in kwargs.items():
                if type(v) is not str:
                    continue
                try:
                    self._kwargs[k] = v.format(*value_opts)
                except IndexError:
                    pass

    @staticmethod
    def from_config(name: str, config: Dict[str, str]) -> Any:
        return Modifier.CLS_MAPPING[config["type"]](name=name, **config)

    def apply_value_opts(self, value_opts):
        return type(self)(value_opts=value_opts, **self.__original_kwargs)

    def __str__(self) -> str:
        return "Modifier {}".format(self.name)


@register(Modifier)
class ModifierSet(Modifier):
    def __init__(self, value_opts=None, **kwargs):
        super().__init__(value_opts, **kwargs)
        self.val = self._kwargs["val"].split("|")

    def flatten(self, configuration: 'Configuration') -> List[Modifier]:
        return parse_modifier_strs(configuration, self.val)

    def __str__(self) -> str:
        return "{} ModifierSet {}".format(super().__str__(), "|".join(self.val))


@register(Modifier)
class JVMArg(Modifier):
    def __init__(self, value_opts=None, **kwargs):
        super().__init__(value_opts, **kwargs)
        self.val = split_quoted(self._kwargs["val"])

    def __str__(self) -> str:
        return "{} JVMArg {}".format(super().__str__(), self.val)


@register(Modifier)
class JVMClasspathAppend(Modifier):
    def __init__(self, value_opts=None, **kwargs):
        super().__init__(value_opts, **kwargs)
        self.val = split_quoted(self._kwargs["val"])

    def __str__(self) -> str:
        return "{} JVMClasspathAppend {}".format(super().__str__(), self.val)


@register(Modifier)
class JVMClasspath(JVMClasspathAppend):
    # backward compatibility
    pass


@register(Modifier)
class JVMClasspathPrepend(Modifier):
    def __init__(self, value_opts=None, **kwargs):
        super().__init__(value_opts, **kwargs)
        self.val = split_quoted(self._kwargs["val"])

    def __str__(self) -> str:
        return "{} JVMClasspathPrepend {}".format(super().__str__(), self.val)


@register(Modifier)
class EnvVar(Modifier):
    def __init__(self, value_opts=None, **kwargs):
        super().__init__(value_opts, **kwargs)
        if "var" not in self._kwargs:
            raise ValueError(
                "Please specify the name of the environment variable for modifier {}".format(self.name))
        if "val" not in self._kwargs:
            raise ValueError(
                "Please specify the value for the environment variable for modifier {}".format(self.name))
        self.var = self._kwargs["var"]
        self.val = self._kwargs["val"]

    def __str__(self) -> str:
        return "{} EnvVar {}={}".format(super().__str__(), self.var, smart_quote(self.val))


@register(Modifier)
class ProgramArg(Modifier):
    def __init__(self, value_opts=None, **kwargs):
        super().__init__(value_opts, **kwargs)
        self.val = split_quoted(self._kwargs["val"])

    def __str__(self) -> str:
        return "{} ProgramArg {}".format(super().__str__(), self.val)


@register(Modifier)
class Wrapper(Modifier):
    def __init__(self, value_opts=None, **kwargs):
        super().__init__(value_opts, **kwargs)
        self.val = split_quoted(self._kwargs["val"])

    def __str__(self) -> str:
        return "{} Wrapper {}".format(super().__str__(), self.val)


@register(Modifier)
class JSArg(Modifier):
    def __init__(self, value_opts=None, **kwargs):
        super().__init__(value_opts, **kwargs)
        self.val = split_quoted(self._kwargs["val"])

    def __str__(self) -> str:
        return "{} JSArg {}".format(super().__str__(), self.val)


@register(Modifier)
class Companion(Modifier):
    def __init__(self, value_opts=None, **kwargs):
        super().__init__(value_opts, **kwargs)
        self.val = split_quoted(self._kwargs["val"])

    def __str__(self) -> str:
        return "{} Companion {}".format(super().__str__(), self.val)
