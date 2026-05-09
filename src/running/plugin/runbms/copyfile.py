import os
import shutil
import stat
from typing import TYPE_CHECKING

from running.command.runbms import get_filename_no_ext
from running.plugin.runbms import RunbmsPlugin
from running.suite import is_dry_run
from running.util import register

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
        self.patterns: list[str]
        self.patterns = kwargs.get("patterns", [])
        if type(self.patterns) is not list:
            raise TypeError("patterns of CopyFile must be a list")
        self.skip_failed = kwargs.get("skip_failed", True)
        if type(self.skip_failed) is not bool:
            raise TypeError("skip_failed of CopyFile must be a bool")

    def __str__(self) -> str:
        return f"CopyFile {self.name}"

    def start_hfac(self, hfac: float | None):
        if self.nop:
            return

    def end_hfac(self, hfac: float | None):
        if self.nop:
            return

    def start_benchmark(self, hfac: float | None, size: int | None, bm: "Benchmark"):
        if self.nop:
            return

    def end_benchmark(self, hfac: float | None, size: int | None, bm: "Benchmark"):
        if self.nop:
            return

    def start_invocation(
        self,
        hfac: float | None,
        size: int | None,
        bm: "Benchmark",
        invocation: int,
    ):
        if self.nop:
            return

    def end_invocation(
        self,
        hfac: float | None,
        size: int | None,
        bm: "Benchmark",
        invocation: int,
    ):
        if self.nop:
            return

    def start_config(
        self,
        hfac: float | None,
        size: int | None,
        bm: "Benchmark",
        invocation: int,
        config: str,
        config_index: int,
    ):
        if self.nop:
            return

    def end_config(
        self,
        hfac: float | None,
        size: int | None,
        bm: "Benchmark",
        invocation: int,
        config: str,
        config_index: int,
        passed: bool,
    ):
        if self.nop:
            return
        if self.runbms_dir is None:
            raise ValueError("runbms_dir should be set")
        if self.log_dir is None:
            raise ValueError("log_dir should be set")
        folder_name = f"{get_filename_no_ext(bm, hfac, size, config)}.{invocation}"
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
