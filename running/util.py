from typing import Any, List, TYPE_CHECKING, Tuple
if TYPE_CHECKING:
    from running.config import Configuration
    from running.modifier import Modifier
    from running.runtime import Runtime

import shlex


def register(parent_class):
    def inner(cls):
        parent_class.CLS_MAPPING[cls.__name__] = cls
        return cls
    return inner


def parse_modifier_strs(configuration: 'Configuration', mod_strs: List[str]) -> List['Modifier']:
    # Some modifiers could be a modifier set, and we need to flatten it
    from running.modifier import ModifierSet
    mods = []
    for m in mod_strs:
        mod_name = m.split("-")[0]
        mod_value_opts = m.split("-")[1:]
        mod = configuration.get("modifiers").get(mod_name)
        if mod is None:
            raise KeyError("Modifier '{}' not defined".format(mod_name))
        mod = mod.apply_value_opts(mod_value_opts)
        if isinstance(mod, ModifierSet):
            for m_inner in mod.flatten(configuration):
                mods.append(m_inner)
        else:
            mods.append(mod)
    return mods


def parse_config_str(configuration: 'Configuration', c: str) -> Tuple['Runtime', List['Modifier']]:
    runtime = configuration.get("runtimes")[c.split('|')[0]]
    mods = parse_modifier_strs(configuration, c.split('|')[1:])
    return runtime, mods


def split_quoted(s: str) -> List[str]:
    return shlex.split(s)


def smart_quote(_s: Any) -> str:
    s = str(_s)
    if s == "":
        return "\"\""
    need_quote = False
    for c in s:
        if not (c.isalnum() or c in '.:/+=-_'):
            need_quote = True
            break
    if need_quote:
        return "\"{}\"".format(s)
    else:
        return s
