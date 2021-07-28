from pathlib import Path
from typing import Any, Dict, Optional, Union
from running.benchmark import JavaBenchmark, BinaryBenchmark
import logging
from running.util import register, split_quoted

__DRY_RUN = False


def is_dry_run():
    global __DRY_RUN
    return __DRY_RUN


def set_dry_run(val: bool):
    global __DRY_RUN
    __DRY_RUN = val


class BenchmarkSuite(object):
    CLS_MAPPING: Dict[str, Any]
    CLS_MAPPING = {}

    def __init__(self, name: str, **kwargs):
        self.name = name

    def __str__(self) -> str:
        return "Benchmark Suite {}".format(self.name)

    def get_benchmark(self, bm_name: str) -> Any:
        raise NotImplementedError()

    @staticmethod
    def from_config(name: str, config: Dict[str, str]) -> Any:
        return BenchmarkSuite.CLS_MAPPING[config["type"]](name=name, **config)

    def is_oom(self, _output: str) -> bool:
        raise NotImplementedError

    def get_minheap(self, _bm_name: str) -> int:
        raise NotImplementedError

    def get_timeout(self, _bm_name: str) -> Optional[int]:
        # No timeout by default
        return None

    def is_passed(self, _output: str) -> bool:
        raise NotImplementedError

    def get_wrapper(self, _bm_name: str) -> Optional[str]:
        return None


@register(BenchmarkSuite)
class BinaryBenchmarkSuite(BenchmarkSuite):
    def __init__(self, programs: Dict[str, Dict[str, str]], **kwargs):
        super().__init__(**kwargs)
        self.programs: Dict[str, Dict[str, Any]]
        self.programs = {
            k: {
                'path': Path(v['path']),
                'args': split_quoted(v['args'])
            }
            for k, v in programs.items()
        }
        self.timeout = kwargs.get("timeout")

    def get_benchmark(self, bm_name: str) -> 'BinaryBenchmark':
        return BinaryBenchmark(
            self.programs[bm_name]['path'],
            self.programs[bm_name]['args'],
            suite_name=self.name,
            bm_name=bm_name
        )

    def is_oom(self, _output: str) -> bool:
        return False

    def get_timeout(self, _bm_name: str) -> Optional[int]:
        # FIXME have per benchmark timeout
        return self.timeout

    def get_minheap(self, _bm_name: str) -> int:
        logging.warning("minheap is not respected for BinaryBenchmarkSuite")
        return 0

    def is_passed(self, _output: str) -> bool:
        # FIXME no generic way to know
        return True


class JavaBenchmarkSuite(BenchmarkSuite):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def get_minheap(self, bm_name: str) -> int:
        raise NotImplementedError()

    def get_timeout(self, bm_name: str) -> Optional[int]:
        raise NotImplementedError()

    def is_oom(self, output: str) -> bool:
        for pattern in ["Allocation Failed", "OutOfMemoryError", "ran out of memory"]:
            if pattern in output:
                return True
        return False


@register(BenchmarkSuite)
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
        self.timeout = kwargs.get("timeout")
        self.wrapper: Optional[Union[Dict[str, str], str]]
        self.wrapper = kwargs.get("wrapper")

    def __str__(self) -> str:
        return "{} DaCapo {} {}".format(super().__str__(), self.release, self.path)

    def get_benchmark(self, bm_name: str) -> 'JavaBenchmark':
        if self.callback:
            cp = [str(self.path)]
            program_args = ["Harness", "-c", self.callback]
        else:
            cp = []
            program_args = ["-jar", str(self.path)]
        program_args.extend(["-n", str(self.timing_iteration), bm_name])
        return JavaBenchmark(
            jvm_args=[],
            program_args=program_args,
            cp=cp,
            wrapper=self.get_wrapper(bm_name),
            suite_name=self.name,
            bm_name=bm_name
        )

    def get_minheap(self, bm_name: str) -> int:
        if bm_name not in self.minheap:
            logging.warn("Minheap for {} of {} not set".format(bm_name, self))
            return 4096
        return self.minheap[bm_name]

    def get_timeout(self, _bm_name: str) -> int:
        # FIXME have per benchmark timeout
        return self.timeout

    def is_passed(self, output: str) -> bool:
        return "PASSED" in output

    def get_wrapper(self, bm_name: str) -> Optional[str]:
        if self.wrapper is None:
            return None
        elif type(self.wrapper) == str:
            return self.wrapper
        elif type(self.wrapper) == dict:
            return self.wrapper.get(bm_name)
        else:
            raise TypeError("wrapper of {} must be either null, "
                            "a string (the same wrapper for all benchmarks), "
                            "or a dictionary (different wrappers for"
                            "differerent benchmarks)".format(self.name))