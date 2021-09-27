from typing import Any, Dict, Optional, TYPE_CHECKING
if TYPE_CHECKING:
    from running.benchmark import Benchmark


class RunbmsPlugin(object):
    CLS_MAPPING: Dict[str, Any]
    CLS_MAPPING = {}

    def __init__(self, **kwargs):
        self.name = kwargs["name"]
        self.run_id = None

    def set_run_id(self, run_id: str):
        self.run_id = run_id

    @staticmethod
    def from_config(name: str, config: Dict[str, str]) -> Any:
        return RunbmsPlugin.CLS_MAPPING[config["type"]](name=name, **config)

    def __str__(self) -> str:
        return "RunbmsPlugin {}".format(self.name)

    def start_hfac(self, _hfac: Optional[float]):
        pass

    def end_hfac(self, _hfac: Optional[float]):
        pass

    def start_benchmark(self, _hfac: Optional[float], _bm: "Benchmark"):
        pass

    def end_benchmark(self, _hfac: Optional[float], _bm: "Benchmark"):
        pass

# !!! Do NOT remove this import nor change its position
# This is to make sure that the Zulip class is correctly registered
from running.plugin.runbms.zulip import Zulip
