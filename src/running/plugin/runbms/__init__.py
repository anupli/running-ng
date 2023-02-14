from pathlib import Path
from typing import Any, Dict, Optional, TYPE_CHECKING
if TYPE_CHECKING:
    from running.benchmark import Benchmark


class RunbmsPlugin(object):
    CLS_MAPPING: Dict[str, Any]
    CLS_MAPPING = {}

    def __init__(self, **kwargs):
        self.name = kwargs["name"]
        self.run_id = None
        self.runbms_dir: Optional[Path]
        self.runbms_dir = None
        self.log_dir: Optional[Path]
        self.log_dir = None

    def set_run_id(self, run_id: Path):
        self.run_id = run_id

    def set_runbms_dir(self, runbms_dir: str):
        self.runbms_dir = Path(runbms_dir).resolve()

    def set_log_dir(self, log_dir: Path):
        self.log_dir = log_dir

    @staticmethod
    def from_config(name: str, config: Dict[str, str]) -> Any:
        return RunbmsPlugin.CLS_MAPPING[config["type"]](name=name, **config)

    def __str__(self) -> str:
        return "RunbmsPlugin {}".format(self.name)

    def start_hfac(self, _hfac: Optional[float]):
        pass

    def end_hfac(self, _hfac: Optional[float]):
        pass

    def start_benchmark(self, _hfac: Optional[float], _size: Optional[int], _bm: "Benchmark"):
        pass

    def end_benchmark(self, _hfac: Optional[float], _size: Optional[int], _bm: "Benchmark"):
        pass

    def start_invocation(self, _hfac: Optional[float], _size: Optional[int], _bm: "Benchmark", _invocation: int):
        pass

    def end_invocation(self, _hfac: Optional[float], _size: Optional[int], _bm: "Benchmark", _invocation: int):
        pass

    def start_config(self, _hfac: Optional[float], _size: Optional[int], _bm: "Benchmark", _invocation: int, _config: str, _config_index: int):
        pass

    def end_config(self, _hfac: Optional[float], _size: Optional[int], _bm: "Benchmark", _invocation: int, _config: str, _config_index: int, _passed: bool):
        pass


# !!! Do NOT remove this import nor change its position
# This is to make sure that the plugin classes are correctly registered
from running.plugin.runbms.copyfile import CopyFile
if TYPE_CHECKING:
    from running.plugin.runbms.zulip import Zulip
else:
    try:
        from running.plugin.runbms.zulip import Zulip
    except:
        from running.util import register

        @register(RunbmsPlugin)
        class Zulip(RunbmsPlugin):
            def __init__(self, **kwargs):
                raise RuntimeError("Trying to create an instance of the Zulip "
                                   "plugin for runbms, but the import failed. "
                                   "This is most likely due to the required "
                                   "dependencies not being installed. Try pip "
                                   "install running-ng[zulip] to install the extra dependencies.")
