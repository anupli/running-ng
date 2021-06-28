from typing import Any, Dict


def register(parent_class):
    def inner(cls):
        parent_class.CLS_MAPPING[cls.__name__] = cls
        return cls
    return inner

def parse_config_str(configuration: Dict[str, Any], c: str):
    jvm = configuration.get("jvms")[c.split('|')[0]]
    mods = [configuration.get("modifiers")[x.split("-")[0]].apply_value_opts(x.split("-")[1:])
            for x in c.split('|')[1:]]
    return jvm, mods
