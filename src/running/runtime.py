from running.modifier import JVMArg, Modifier, JSArg, EnvVar
from typing import Any, Dict, List, Union
from pathlib import Path
import logging
from running.util import register
import os.path


class Runtime(object):
    CLS_MAPPING: Dict[str, Any]
    CLS_MAPPING = {}

    def __init__(self, name: str, **kwargs):
        self.name = name

    @staticmethod
    def from_config(name: str, config: Dict[str, str]) -> Any:
        return Runtime.CLS_MAPPING[config["type"]](name=name, **config)

    def get_executable(self) -> Union[str, Path]:
        raise NotImplementedError

    def get_heapsize_modifiers(self, size: int) -> List[Modifier]:
        raise NotImplementedError

    def is_oom(self, _output: bytes) -> bool:
        raise NotImplementedError


class DummyRuntime(Runtime):
    def __init__(self, executable: str):
        super().__init__(name="dummy")
        self.executable = executable

    def get_executable(self) -> Union[str, Path]:
        return self.executable

    def is_oom(self, _output: bytes) -> bool:
        return False


@register(Runtime)
class NativeExecutable(Runtime):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def get_executable(self) -> Union[str, Path]:
        return ""

    def is_oom(self, _output: bytes) -> bool:
        return False


class JVM(Runtime):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def get_executable(self) -> Path:
        raise NotImplementedError

    def __str__(self):
        return "JVM {}".format(self.name)

    def get_heapsize_modifiers(self, size: int) -> List[Modifier]:
        size_str = "{}M".format(size)
        heapsize = JVMArg(
            name="heap{}".format(size_str),
            val="-Xms{} -Xmx{}".format(size_str, size_str),
        )
        return [heapsize]

    def is_oom(self, output: bytes) -> bool:
        for pattern in [
            b"Allocation Failed",
            b"OutOfMemoryError",
            b"ran out of memory",
            b"panicked at 'Out of memory!'",
        ]:
            if pattern in output:
                return True
        return False


@register(Runtime)
class OpenJDK(JVM):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.release = kwargs["release"]
        try:
            self.release = int(self.release)
        except ValueError:
            raise TypeError("The release of an OpenJDK has to be int-like")
        self.home: Path
        self.home = Path(os.path.expandvars(kwargs["home"]))
        if not self.home.exists():
            logging.warning("OpenJDK home {} doesn't exist".format(self.home))
        self.executable = self.home / "bin" / "java"
        if not self.executable.exists():
            logging.warning("{} not found in OpenJDK home".format(self.executable))
        self.executable = self.executable.absolute()

    def get_executable(self) -> Path:
        return self.executable

    def __str__(self):
        return "{} OpenJDK {} {}".format(super().__str__(), self.release, self.home)


@register(Runtime)
class JikesRVM(JVM):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.home: Path
        self.home = Path(os.path.expandvars(kwargs["home"]))
        if not self.home.exists():
            logging.warning("JikesRVM home {} doesn't exist".format(self.home))
        self.executable = self.home / "rvm"
        if not self.home.exists():
            logging.warning("{} not found in JikesRVM home".format(self.executable))
        self.executable = self.executable.absolute()

    def get_executable(self) -> Path:
        return self.executable

    def __str__(self):
        return "{} JikesRVM {}".format(super().__str__(), self.home)


class JavaScriptRuntime(Runtime):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.executable: Path
        self.executable = Path(os.path.expandvars(kwargs["executable"]))
        if not self.executable.exists():
            logging.warning(
                "JavaScriptRuntime executable {} doesn't exist".format(self.executable)
            )
        self.executable = self.executable.absolute()

    def get_executable(self) -> Path:
        return self.executable


@register(Runtime)
class D8(JavaScriptRuntime):
    def __str__(self):
        return "{} d8 {}".format(super().__str__(), self.executable)

    def get_heapsize_modifiers(self, size: int) -> List[Modifier]:
        size_str = "{}".format(size)
        heapsize = JSArg(
            name="heap{}".format(size_str),
            val="--initial-heap-size={} --max-heap-size={}".format(size_str, size_str),
        )
        return [heapsize]

    def is_oom(self, output: bytes) -> bool:
        # The format is "Fatal javascript OOM in ..." or "Fatal JavaScript out of memory"
        # such as "Fatal javascript OOM in Reached heap limit"
        # or "Fatal javascript OOM in Ineffective mark-compacts near heap limit"
        # or "Fatal JavaScript out of memory: Reached heap limit"
        for pattern in [b"Fatal javascript OOM in", b"Fatal JavaScript out of memory"]:
            if pattern in output:
                return True
        return False

@register(Runtime)
class Chrome(JavaScriptRuntime):
    def __str__(self):
        return "{} chrome {}".format(super().__str__(), self.executable)

    def get_heapsize_modifiers(self, size: int) -> List[Modifier]:
        size_str = "{}".format(size)
        heapsize = JSArg(
            name="heap{}".format(size_str),
            val="--initial-heap-size={} --max-heap-size={}".format(
                size_str, size_str)
        )
        return [heapsize]

    def is_oom(self, output: bytes) -> bool:
        for pattern in [b"Fatal javascript OOM in", b"Fatal JavaScript out of memory", b"V8 javascript OOM", b"<--- Last few GCs --->"]:
            if pattern in output:
                return True
        return False

@register(Runtime)
class SpiderMonkey(JavaScriptRuntime):
    def __str__(self):
        return "{} SpiderMonkey {}".format(super().__str__(), self.executable)

    def get_heapsize_modifiers(self, size: int) -> List[Modifier]:
        size_str = "{}".format(size)
        # FIXME doesn't seem to be working
        heapsize = JSArg(
            name="heap{}".format(size_str), val="--available-memory={}".format(size_str)
        )
        return [heapsize]

    def is_oom(self, output: bytes) -> bool:
        # FIXME not sure how to check for OOM for SpiderMonkey yet
        return False


@register(Runtime)
class JavaScriptCore(JavaScriptRuntime):
    def __str__(self):
        return "{} JavaScriptCore {}".format(super().__str__(), self.executable)

    def get_heapsize_modifiers(self, size: int) -> List[Modifier]:
        size_str = "{}".format(size)
        # FIXME doesn't seem to be working
        heapsize = JSArg(
            name="heap{}".format(size_str), val="--gcMaxHeapSize={}".format(size_str)
        )
        return [heapsize]

    def is_oom(self, output: bytes) -> bool:
        # FIXME not sure how to check for OOM for JavaScriptCore yet
        return False


class Julia(Runtime):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.executable: Path
        self.executable = Path(os.path.expandvars(kwargs["executable"]))
        if not self.executable.exists():
            logging.warning("Julia executable {} doesn't exist".format(self.executable))
        self.executable = self.executable.absolute()

    def get_executable(self) -> Path:
        return self.executable

    def __str__(self):
        return "Julia {} {}".format(self.name, self.executable)


@register(Runtime)
class JuliaMMTK(Julia):
    def get_heapsize_modifiers(self, size: int) -> List[Modifier]:
        # size in MB
        size_str = "{}".format(size)
        min = EnvVar(
            name="minheap{}".format(size_str), var="MMTK_MIN_HSIZE", val=size_str
        )
        max = EnvVar(
            name="maxheap{}".format(size_str), var="MMTK_MAX_HSIZE", val=size_str
        )
        return [min, max]

    def __str__(self):
        return "{} with MMTk".format(super().__str__())

    def is_oom(self, output: bytes) -> bool:
        return b"Out of Memory!" in output


@register(Runtime)
class JuliaStock(Julia):
    def get_heapsize_modifiers(self, size: int) -> List[Modifier]:
        return []

    def __str__(self):
        return "{} stock version".format(super().__str__())

    def is_oom(self, output: bytes) -> bool:
        return False
