from typing import Any, List, TYPE_CHECKING
if TYPE_CHECKING:
    from running.config import Configuration

import shlex


def register(parent_class):
    def inner(cls):
        parent_class.CLS_MAPPING[cls.__name__] = cls
        return cls
    return inner


def parse_config_str(configuration: 'Configuration', c: str):
    runtime = configuration.get("runtimes")[c.split('|')[0]]
    mods = [configuration.get("modifiers")[x.split("-")[0]].apply_value_opts(x.split("-")[1:])
            for x in c.split('|')[1:]]
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
