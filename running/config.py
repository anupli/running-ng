from typing import Any, Dict, List, Tuple, Tuple, TypeVar
import yaml
from running.benchmark import JavaBenchmarkSuite, JavaProgram
from running.jvm import JVM
from running.modifier import Modifier


class Configuration(object):
    def __init__(self, suites: Dict[str, JavaBenchmarkSuite], modifiers: Dict[str, Modifier], jvms: Dict[str, JVM], benchmarks: List[JavaProgram], configs: List[str], invocations: int):
        self.suites = suites
        self.modifiers = modifiers
        self.jvms = jvms
        self.benchmarks = benchmarks
        self.configs = configs
        self.invocations = invocations


def load_class(cls: Any, config: Dict[str, Dict[str, str]]) -> Dict[str, Any]:
    return {k: cls.from_config(k, v) for (k, v) in config.items()}


def load_all(config_path) -> Configuration:
    assert config_path.exists()
    with config_path.open("r") as fd:
        config = yaml.safe_load(fd)
        suites = load_class(JavaBenchmarkSuite, config["suites"])
        modifiers = load_class(Modifier, config["modifiers"])
        jvms = load_class(JVM, config["jvms"])
        benchmarks = []
        for s, bms in config["benchmarks"].items():
            suite = suites[s]
            for b in bms:
                benchmarks.append(suite.get_benchmark(b))
        configs = config["configs"]
        invocations = config["invocations"]
    return Configuration(suites, modifiers, jvms, benchmarks, configs, invocations)
