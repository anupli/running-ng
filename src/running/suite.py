import logging
import os.path
from pathlib import Path
from typing import Any

from running.benchmark import (
    Benchmark,
    BinaryBenchmark,
    JavaBenchmark,
    JavaScriptBenchmark,
    JuliaBenchmark,
)
from running.util import register, split_quoted

__DRY_RUN = False
DEFAULT_MINHEAP = 4096


def is_dry_run():
    global __DRY_RUN
    return __DRY_RUN


def set_dry_run(val: bool):
    global __DRY_RUN
    __DRY_RUN = val


def parse_timing_iteration(t: str | None, suite_name: str) -> str | int:
    if not t:
        raise KeyError(
            f"You need to specify the timing_iteration for a {suite_name} suite"
        )
    assert t is not None
    try:
        t_parsed = int(t)
        return t_parsed
    except ValueError:
        return t


class BenchmarkSuite:
    CLS_MAPPING: dict[str, Any]
    CLS_MAPPING = {}

    def __init__(self, name: str, **kwargs):
        self.name = name

    def __str__(self) -> str:
        return f"Benchmark Suite {self.name}"

    @staticmethod
    def from_config(name: str, config: dict[str, str]) -> Any:
        return BenchmarkSuite.CLS_MAPPING[config["type"]](name=name, **config)

    def get_benchmark(self, bm_spec: str | dict[str, Any]) -> Any:
        raise NotImplementedError()

    def get_minheap(self, bm: Benchmark) -> int:
        raise NotImplementedError

    def is_passed(self, output: bytes) -> bool:
        raise NotImplementedError


@register(BenchmarkSuite)
class BinaryBenchmarkSuite(BenchmarkSuite):
    def __init__(self, programs: dict[str, dict[str, str]], **kwargs):
        super().__init__(**kwargs)
        self.programs: dict[str, dict[str, Any]]
        self.programs = {
            k: {"path": Path(v["path"]), "args": split_quoted(v["args"])}
            for k, v in programs.items()
        }
        self.timeout = kwargs.get("timeout")

    def get_benchmark(self, bm_spec: str | dict[str, Any]) -> "BinaryBenchmark":
        assert type(bm_spec) is str
        bm_name = bm_spec
        return BinaryBenchmark(
            self.programs[bm_name]["path"],
            self.programs[bm_name]["args"],
            suite_name=self.name,
            name=bm_name,
            timeout=self.timeout,
        )

    def get_minheap(self, bm: Benchmark) -> int:
        logging.warning("minheap is not respected for BinaryBenchmarkSuite")
        assert isinstance(bm, BinaryBenchmark)
        return 0

    def is_passed(self, output: bytes) -> bool:
        # FIXME no generic way to know
        return True


class JavaBenchmarkSuite(BenchmarkSuite):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def get_minheap(self, bm: Benchmark) -> int:
        raise NotImplementedError()


@register(BenchmarkSuite)
class DaCapo(JavaBenchmarkSuite):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.release: str
        self.release = kwargs["release"]
        if self.release not in ["2006", "9.12", "evaluation", "23.11"]:
            raise ValueError(f"DaCapo release {self.release} not recognized")
        self.path: Path
        self.path = Path(os.path.expandvars(kwargs["path"]))
        if not self.path.exists():
            logging.warning(f"DaCapo jar {self.path} not found")
        self.minheap: str | None
        self.minheap = kwargs.get("minheap")
        self.minheap_values: dict[str, dict[str, int]]
        self.minheap_values = kwargs.get("minheap_values", {})
        if not isinstance(self.minheap_values, dict):
            raise TypeError(f"The minheap_values of {self.name} should be a dictionary")
        if self.minheap:
            if not isinstance(self.minheap, str):
                raise TypeError(
                    f"The minheap of {self.name} should be a"
                    " string that selects from a minheap_values"
                )
            if self.minheap not in self.minheap_values:
                raise KeyError(
                    f"{self.name} is not a valid entry of {self.name}.minheap_values"
                )
        self.timing_iteration = parse_timing_iteration(
            kwargs.get("timing_iteration"), "DaCapo"
        )
        if (
            isinstance(self.timing_iteration, str)
            and self.timing_iteration != "converge"
        ):
            raise TypeError(
                f"The timing iteration of the DaCapo benchmark"
                f" suite `{self.path}` is"
                f" {repr(self.timing_iteration)}, which neither"
                " an integer nor 'converge'"
            )
        self.callback: str | None
        self.callback = kwargs.get("callback")
        self.timeout: int | None
        self.timeout = kwargs.get("timeout")
        self.wrapper: dict[str, str] | str | None
        self.wrapper = kwargs.get("wrapper")
        self.companion: dict[str, str] | str | None
        self.companion = kwargs.get("companion")
        # user overriding the default size for the entire suite
        self.size: str | None
        self.size = kwargs.get("size")

    def __str__(self) -> str:
        return f"{super().__str__()} DaCapo {self.release} {self.path}"

    @staticmethod
    def parse_timing_iteration(v: Any):
        try:
            timing_iteration = int(v)
        except ValueError:
            if v != "converge":
                raise TypeError(
                    f"The timing iteration {repr(v)} is neither"
                    " an integer nor 'converge'"
                )
            timing_iteration = v
        return timing_iteration

    def get_benchmark(self, bm_spec: str | dict[str, Any]) -> "JavaBenchmark":
        timing_iteration = self.timing_iteration
        timeout = self.timeout
        size = self.size
        if type(bm_spec) is str:
            bm_name = bm_spec
            name = bm_spec
        else:
            assert type(bm_spec) is dict
            if "bm_name" not in bm_spec or "name" not in bm_spec:
                raise KeyError(
                    "When a dictionary is used to specify a"
                    " benchmark, you need to provide both"
                    " `name` and `bm_name`"
                )
            bm_name = bm_spec["bm_name"]
            name = bm_spec["name"]
            if "timing_iteration" in bm_spec:
                timing_iteration = DaCapo.parse_timing_iteration(
                    bm_spec["timing_iteration"]
                )
            # user overriding the size for that benchmark
            if "size" in bm_spec:
                size = bm_spec["size"]
            if "timeout" in bm_spec:
                timeout = bm_spec["timeout"]

        if self.callback:
            cp = [str(self.path)]
            program_args = ["Harness", "-c", self.callback]
        else:
            cp = []
            program_args = ["-jar", str(self.path)]
        # Timing iteration
        if type(timing_iteration) is int:
            program_args.extend(["-n", str(timing_iteration)])
        else:
            assert timing_iteration == "converge"
            if self.release == "2006":
                program_args.append("-converge")
            else:
                program_args.append("--converge")
        # Input size
        if size:
            program_args.extend(["-s", size])
        # Name of the benchmark
        program_args.append(bm_name)

        return JavaBenchmark(
            jvm_args=[],
            program_args=program_args,
            cp=cp,
            wrapper=self.get_wrapper(bm_name),
            companion=self.get_companion(bm_name),
            suite_name=self.name,
            name=name,
            timeout=timeout,
        )

    def get_minheap(self, bm: Benchmark) -> int:
        assert isinstance(bm, JavaBenchmark)
        name = bm.name
        if not self.minheap:
            logging.warning(f"No minheap_value of {self} is selected")
            return DEFAULT_MINHEAP
        minheap = self.minheap_values[self.minheap]
        if name not in minheap:
            logging.warning(f"Minheap for {name} of {self} not set")
            return DEFAULT_MINHEAP
        return minheap[name]

    def is_passed(self, output: bytes) -> bool:
        return b"PASSED" in output

    def get_wrapper(self, bm_name: str) -> str | None:
        if self.wrapper is None:
            return None
        elif type(self.wrapper) is str:
            return self.wrapper
        elif type(self.wrapper) is dict:
            return self.wrapper.get(bm_name)
        else:
            raise TypeError(
                f"wrapper of {self.name} must be either null, "
                "a string (the same wrapper for all benchmarks), "
                "or a dictionary (different wrappers for"
                "differerent benchmarks)"
            )

    def get_companion(self, bm_name: str) -> str | None:
        if self.companion is None:
            return None
        elif type(self.companion) is str:
            return self.companion
        elif type(self.companion) is dict:
            return self.companion.get(bm_name)
        else:
            raise TypeError(
                f"companion of {self.name} must be either null, "
                "a string (the same companion for all benchmarks), "
                "or a dictionary (different companions for"
                "differerent benchmarks)"
            )


@register(BenchmarkSuite)
class SPECjbb2015(JavaBenchmarkSuite):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.release: str
        self.release = kwargs["release"]
        if self.release not in ["1.03"]:
            raise ValueError(f"SPECjbb2015 release {self.release} not recognized")
        self.path: Path
        self.path = Path(os.path.expandvars(kwargs["path"])).resolve()
        self.propsfile = (self.path / ".." / "config" / "specjbb2015.props").resolve()
        if not self.path.exists():
            logging.info(f"SPECjbb2015 jar {self.path} not found")

    def __str__(self) -> str:
        return f"{super().__str__()} SPECjbb2015 {self.release} {self.path}"

    def get_benchmark(self, bm_spec: str | dict[str, Any]) -> "JavaBenchmark":
        assert type(bm_spec) is str
        if bm_spec != "composite":
            raise ValueError("Only composite mode is supported for now")

        program_args = [
            "-jar",
            str(self.path),
            "-p",
            str(self.propsfile),
            "-m",
            "COMPOSITE",
            "-skipReport",
        ]
        return JavaBenchmark(
            jvm_args=[],
            program_args=program_args,
            cp=[],
            suite_name=self.name,
            name="composite",
        )

    def get_minheap(self, bm: Benchmark) -> int:
        return 2048  # SPEC recommends running with minimum 2GB of heap

    def is_passed(self, output: bytes) -> bool:
        # FIXME
        return True


@register(BenchmarkSuite)
class Octane(BenchmarkSuite):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.path: Path
        self.path = Path(os.path.expandvars(kwargs["path"])).resolve()
        if not self.path.exists():
            logging.info(f"Octane folder {self.path} not found")
        self.wrapper: Path
        self.wrapper = Path(kwargs["wrapper"]).resolve()
        if not self.wrapper.exists():
            logging.info(f"Octane folder {self.wrapper} not found")
        timing_iteration = parse_timing_iteration(
            kwargs.get("timing_iteration"), "Octane"
        )
        self.timing_iteration: int
        if isinstance(timing_iteration, str):
            raise TypeError("timing_iteration for Octane has to be an integer")
        else:
            self.timing_iteration = timing_iteration
        self.minheap: str | None
        self.minheap = kwargs.get("minheap")
        self.minheap_values: dict[str, dict[str, int]]
        self.minheap_values = kwargs.get("minheap_values", {})
        if not isinstance(self.minheap_values, dict):
            raise TypeError(f"The minheap_values of {self.name} should be a dictionary")
        if self.minheap:
            if not isinstance(self.minheap, str):
                raise TypeError(
                    f"The minheap of {self.name} should be a"
                    " string that selects from a minheap_values"
                )
            if self.minheap not in self.minheap_values:
                raise KeyError(
                    f"{self.name} is not a valid entry of {self.name}.minheap_values"
                )
        self.timeout: int | None
        self.timeout = kwargs.get("timeout")

    def __str__(self) -> str:
        return f"{super().__str__()} Octane {self.path}"

    def get_benchmark(self, bm_spec: str | dict[str, Any]) -> "JavaScriptBenchmark":
        assert type(bm_spec) is str

        program_args = [str(self.path), bm_spec, str(self.timing_iteration)]
        return JavaScriptBenchmark(
            js_args=[],
            program=str(self.wrapper),
            program_args=program_args,
            suite_name=self.name,
            name=bm_spec,
            timeout=self.timeout,
        )

    def get_minheap(self, bm: Benchmark) -> int:
        assert isinstance(bm, JavaScriptBenchmark)
        name = bm.name
        if not self.minheap:
            logging.warning(f"No minheap_value of {self} is selected")
            return DEFAULT_MINHEAP
        minheap = self.minheap_values[self.minheap]
        if name not in minheap:
            logging.warning(f"Minheap for {name} of {self} not set")
            return DEFAULT_MINHEAP
        return minheap[name]

    def is_passed(self, output: bytes) -> bool:
        return b"PASSED" in output


@register(BenchmarkSuite)
class SPECjvm98(JavaBenchmarkSuite):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.release: str
        self.release = kwargs["release"]
        if self.release not in ["1.03_05"]:
            raise ValueError(f"SPECjvm98 release {self.release} not recognized")
        self.path: Path
        self.path = Path(os.path.expandvars(kwargs["path"])).resolve()

        if not self.path.exists():
            logging.info(f"SPECjvm98 {self.path} not found")
        if not (self.path / "SpecApplication.class").exists():
            logging.info(f"SpecApplication.class not found under SPECjvm98 {self.path}")
        timing_iteration = parse_timing_iteration(
            kwargs.get("timing_iteration"), "SPECjvm98"
        )
        self.timing_iteration: int
        if isinstance(timing_iteration, str):
            raise TypeError("timing_iteration for SPECjvm98 has to be an integer")
        else:
            self.timing_iteration = timing_iteration

    def __str__(self) -> str:
        return f"{super().__str__()} SPECjvm98 {self.release} {self.path}"

    def get_benchmark(self, bm_spec: str | dict[str, Any]) -> "JavaBenchmark":
        assert type(bm_spec) is str
        program_args = [
            "SpecApplication",
            f"-i{self.timing_iteration}",
            bm_spec,
        ]
        return JavaBenchmark(
            jvm_args=[],
            program_args=program_args,
            cp=[str(self.path)],
            suite_name=self.name,
            name=bm_spec,
            override_cwd=self.path,
        )

    def get_minheap(self, bm: Benchmark) -> int:
        # FIXME allow user to measure and specify minimum heap sizes
        return 32  # SPEC recommends running with minimum 32MB of heap

    def is_passed(self, output: bytes) -> bool:
        # FIXME
        return b"**NOT VALID**" not in output


@register(BenchmarkSuite)
class JuliaGCBenchmarks(BenchmarkSuite):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.path: Path
        self.path = Path(os.path.expandvars(kwargs["path"]))
        if not self.path.exists():
            logging.warning(f"JuliaGCBenchmarks does not exist at {self.path}")
        self.minheap: str | None
        self.minheap = kwargs.get("minheap")
        self.minheap_values: dict[str, dict[str, int]]
        self.minheap_values = kwargs.get("minheap_values", {})
        if not isinstance(self.minheap_values, dict):
            raise TypeError(f"The minheap_values of {self.name} should be a dictionary")
        if self.minheap:
            if not isinstance(self.minheap, str):
                raise TypeError(
                    f"The minheap of {self.name} should be a"
                    " string that selects from a minheap_values"
                )
            if self.minheap not in self.minheap_values:
                raise KeyError(
                    f"{self.name} is not a valid entry of {self.name}.minheap_values"
                )
        self.timeout: int | None
        self.timeout = kwargs.get("timeout")

    def __str__(self) -> str:
        return f"{super().__str__()} JuliaGCBenchmarks {self.path}"

    def get_minheap(self, bm: Benchmark) -> int:
        name = bm.name
        if not self.minheap:
            logging.warning(f"No minheap_value of {self} is selected")
            return DEFAULT_MINHEAP
        minheap = self.minheap_values[self.minheap]
        if name not in minheap:
            logging.warning(f"Minheap for {name} of {self} not set")
            return DEFAULT_MINHEAP
        return minheap[name]

    def get_benchmark(self, bm_spec: str | dict[str, Any]) -> "JuliaBenchmark":
        timeout = self.timeout
        if type(bm_spec) is str:
            name = bm_spec
        else:
            assert type(bm_spec) is dict
            if "name" not in bm_spec:
                raise KeyError(
                    "When a dictionary is used to specify a"
                    " benchmark, you need to provide `name`"
                )
            name = bm_spec["name"]
            if "timeout" in bm_spec:
                timeout = bm_spec["timeout"]
        return JuliaBenchmark(
            julia_args=[],
            suite_name=self.name,
            name=name,
            suite_path=self.path,
            program_args=[],
            timeout=timeout,
        )

    def is_passed(self, output: bytes) -> bool:
        # FIXME
        return True
