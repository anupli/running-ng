import os
import stat
from typing import List, Optional, TYPE_CHECKING
from running.plugin.runbms import RunbmsPlugin
from running.command.runbms import get_filename_no_ext
from running.suite import is_dry_run
from running.util import register
import shutil
if TYPE_CHECKING:
    from running.benchmark import Benchmark


def delete_readonly(_function, path, _excinfo):
    os.chmod(path, stat.S_IWRITE)
    os.remove(path)


@register(RunbmsPlugin)
class CopyFile(RunbmsPlugin):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.nop: bool
        self.nop = is_dry_run()
        self.patterns: List[str]
        self.patterns = kwargs.get("patterns", [])
        if type(self.patterns) is not list:
            raise TypeError("patterns of CopyFile must be a list")
        self.skip_failed = kwargs.get("skip_failed", True)
        if type(self.skip_failed) is not bool:
            raise TypeError("skip_failed of CopyFile must be a bool")

    def __str__(self) -> str:
        return "CopyFile {}".format(self.name)

    def start_hfac(self, hfac: Optional[float]):
        if self.nop:
            return

    def end_hfac(self, _hfac: Optional[float]):
        if self.nop:
            return

    def start_benchmark(self, _hfac: Optional[float], _size: Optional[int], bm: "Benchmark"):
        if self.nop:
            return

    def end_benchmark(self, _hfac: Optional[float], _size: Optional[int], bm: "Benchmark"):
        if self.nop:
            return

    def start_invocation(self, _hfac: Optional[float], _size: Optional[int], _bm: "Benchmark", invocation: int):
        if self.nop:
            return

    def end_invocation(self, _hfac: Optional[float], _size: Optional[int], _bm: "Benchmark", _invocation: int):
        if self.nop:
            return

    def start_config(self, _hfac: Optional[float], _size: Optional[int], _bm: "Benchmark", _invocation: int, config: str, _config_index: int):
        if self.nop:
            return

    def end_config(self, hfac: Optional[float], size: Optional[int], bm: "Benchmark", invocation: int, config: str, _config_index: int, passed: bool):
        if self.nop:
            return
        if self.runbms_dir is None:
            raise ValueError("runbms_dir should be set")
        if self.log_dir is None:
            raise ValueError("log_dir should be set")
        folder_name = "{}.{}".format(
            get_filename_no_ext(bm, hfac, size, config),
            invocation
        )
        if self.skip_failed and (not passed):
            # Do nothing if we skip failed invocation and the current invocation
            # didn't pass
            pass
        else:
            target = self.log_dir / folder_name
            target.mkdir(parents=True, exist_ok=True)
            for pattern in self.patterns:
                for file in self.runbms_dir.glob(pattern):
                    shutil.copy2(file, target)
        for child in self.runbms_dir.iterdir():
            if child.is_dir():
                shutil.rmtree(child)
            else:
                child.unlink()
