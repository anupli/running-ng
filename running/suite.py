from pathlib import Path
from typing import Any, Dict
from running.benchmark import JavaBenchmark
import logging
from running.util import register

__DRY_RUN = False


def is_dry_run():
    global __DRY_RUN
    return __DRY_RUN


def set_dry_run(val: bool):
    global __DRY_RUN
    __DRY_RUN = val


class JavaBenchmarkSuite(object):
    CLS_MAPPING: Dict[str, Any]
    CLS_MAPPING = {}

    def __init__(self, **kwargs):
        self.name = kwargs["name"]

    @staticmethod
    def from_config(name: str, config: Dict[str, str]) -> Any:
        return JavaBenchmarkSuite.CLS_MAPPING[config["type"]](name=name, **config)

    def __str__(self) -> str:
        return "Benchmark Suite {}".format(self.name)

    def get_benchmark(self, bm_name: str) -> 'JavaBenchmark':
        raise NotImplementedError()

    def get_minheap(self, bm_name: str) -> int:
        raise NotImplementedError()

    def get_timeout(self, bm_name: str) -> int:
        raise NotImplementedError()


@register(JavaBenchmarkSuite)
class DaCapo(JavaBenchmarkSuite):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.release = kwargs["release"]
        if self.release not in ["2006", "9.12", "evaluation"]:
            logging.info(
                "DaCapo release {} not recongized".format(self.release))
        self.path: Path
        self.path = Path(kwargs["path"])
        if not self.path.exists():
            logging.info("DaCapo jar {} not found".format(self.path))
        self.minheap = kwargs.get("minheap", {})
        try:
            self.timing_iteration = int(kwargs.get("timing_iteration"))
        except TypeError:
            logging.warning(
                "Timing iteration not set for DaCapo {}, use default value 3".format(self.path))
            self.timing_iteration = 3
        self.callback = kwargs.get("callback")

    def __str__(self) -> str:
        return "{} DaCapo {} {}".format(super().__str__(), self.release, self.path)

    def get_benchmark(self, bm_name: str) -> 'JavaBenchmark':
        if self.callback:
            cp = [str(self.path)]
            jvm_args = []
            progam_args = ["Harness", "-c", self.callback]
        else:
            cp = []
            jvm_args = ["-jar", str(self.path)]
            progam_args = []
        progam_args.extend(["-n", str(self.timing_iteration), bm_name])
        return JavaBenchmark(self.name, bm_name, jvm_args, progam_args, cp)

    def get_minheap(self, bm_name: str) -> int:
        if bm_name not in self.minheap:
            logging.warn("Minheap for {} of {} not set".format(bm_name, self))
            return 4096
        return self.minheap[bm_name]

    def get_timeout(self, bm_name: str) -> int:
        # FIXME
        return 120
