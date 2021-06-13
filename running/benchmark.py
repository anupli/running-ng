from pathlib import Path
from typing import Any, Dict

class Benchmark(object):
    def __init__(self, **kwargs):
        self.name = kwargs["name"]
    
    @staticmethod
    def from_config(name: str, config: Dict[str, str]) -> Any:
        return eval(config["type"])(name=name, **config)


class DaCapo(Benchmark):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.release = kwargs["release"]
        assert self.release in ["2006", "9.12"]
        self.path: Path
        self.path = Path(kwargs["path"])
        assert self.path.exists()

