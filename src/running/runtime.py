import logging
import os.path
from pathlib import Path
from typing import Any

from running.modifier import EnvVar, JSArg, JVMArg, Modifier
from running.util import register


class Runtime:
    CLS_MAPPING: dict[str, Any]
    CLS_MAPPING = {}

    def __init__(self, name: str, **kwargs):
        self.name = name

    @staticmethod
    def from_config(name: str, config: dict[str, str]) -> Any:
        return Runtime.CLS_MAPPING[config["type"]](name=name, **config)

    def get_executable(self) -> str | Path:
        raise NotImplementedError

    def get_heapsize_modifiers(self, size: int) -> list[Modifier]:
        raise NotImplementedError

    def is_oom(self, output: bytes) -> bool:
        raise NotImplementedError


class DummyRuntime(Runtime):
    def __init__(self, executable: str):
        super().__init__(name="dummy")
        self.executable = executable

    def get_executable(self) -> str | Path:
        return self.executable

    def is_oom(self, output: bytes) -> bool:
        return False


@register(Runtime)
class NativeExecutable(Runtime):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def get_executable(self) -> str | Path:
        return ""

    def is_oom(self, output: bytes) -> bool:
        return False


class JVM(Runtime):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def get_executable(self) -> Path:
        raise NotImplementedError

    def __str__(self):
        return f"JVM {self.name}"

    def get_heapsize_modifiers(self, size: int) -> list[Modifier]:
        size_str = f"{size}M"
        heapsize = JVMArg(
            name=f"heap{size_str}",
            val=f"-Xms{size_str} -Xmx{size_str}",
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
            logging.warning(f"OpenJDK home {self.home} doesn't exist")
        self.executable = self.home / "bin" / "java"
        if not self.executable.exists():
            logging.warning(f"{self.executable} not found in OpenJDK home")
        self.executable = self.executable.absolute()

    def get_executable(self) -> Path:
        return self.executable

    def __str__(self):
        return f"{super().__str__()} OpenJDK {self.release} {self.home}"


@register(Runtime)
class JikesRVM(JVM):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.home: Path
        self.home = Path(os.path.expandvars(kwargs["home"]))
        if not self.home.exists():
            logging.warning(f"JikesRVM home {self.home} doesn't exist")
        self.executable = self.home / "rvm"
        if not self.home.exists():
            logging.warning(f"{self.executable} not found in JikesRVM home")
        self.executable = self.executable.absolute()

    def get_executable(self) -> Path:
        return self.executable

    def __str__(self):
        return f"{super().__str__()} JikesRVM {self.home}"


class JavaScriptRuntime(Runtime):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.executable: Path
        self.executable = Path(os.path.expandvars(kwargs["executable"]))
        if not self.executable.exists():
            logging.warning(
                f"JavaScriptRuntime executable {self.executable} doesn't exist"
            )
        self.executable = self.executable.absolute()

    def get_executable(self) -> Path:
        return self.executable


@register(Runtime)
class D8(JavaScriptRuntime):
    def __str__(self):
        return f"{super().__str__()} d8 {self.executable}"

    def get_heapsize_modifiers(self, size: int) -> list[Modifier]:
        size_str = f"{size}"
        heapsize = JSArg(
            name=f"heap{size_str}",
            val=f"--initial-heap-size={size_str} --max-heap-size={size_str}",
        )
        return [heapsize]

    def is_oom(self, output: bytes) -> bool:
        # The format is "Fatal javascript OOM in ..."
        # or "Fatal JavaScript out of memory"
        # such as "Fatal javascript OOM in Reached heap limit"
        # or "Fatal javascript OOM in Ineffective mark-compacts
        #     near heap limit"
        # or "Fatal JavaScript out of memory: Reached heap limit"
        for pattern in [
            b"Fatal javascript OOM in",
            b"Fatal JavaScript out of memory",
        ]:
            if pattern in output:
                return True
        return False


@register(Runtime)
class SpiderMonkey(JavaScriptRuntime):
    def __str__(self):
        return f"{super().__str__()} SpiderMonkey {self.executable}"

    def get_heapsize_modifiers(self, size: int) -> list[Modifier]:
        size_str = f"{size}"
        # FIXME doesn't seem to be working
        heapsize = JSArg(name=f"heap{size_str}", val=f"--available-memory={size_str}")
        return [heapsize]

    def is_oom(self, output: bytes) -> bool:
        # FIXME not sure how to check for OOM for SpiderMonkey yet
        return False


@register(Runtime)
class JavaScriptCore(JavaScriptRuntime):
    def __str__(self):
        return f"{super().__str__()} JavaScriptCore {self.executable}"

    def get_heapsize_modifiers(self, size: int) -> list[Modifier]:
        size_str = f"{size}"
        # FIXME doesn't seem to be working
        heapsize = JSArg(name=f"heap{size_str}", val=f"--gcMaxHeapSize={size_str}")
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
            logging.warning(f"Julia executable {self.executable} doesn't exist")
        self.executable = self.executable.absolute()

    def get_executable(self) -> Path:
        return self.executable

    def __str__(self):
        return f"Julia {self.name} {self.executable}"


@register(Runtime)
class JuliaMMTK(Julia):
    def get_heapsize_modifiers(self, size: int) -> list[Modifier]:
        # size in MB
        size_str = f"{size}"
        min = EnvVar(name=f"minheap{size_str}", var="MMTK_MIN_HSIZE", val=size_str)
        max = EnvVar(name=f"maxheap{size_str}", var="MMTK_MAX_HSIZE", val=size_str)
        return [min, max]

    def __str__(self):
        return f"{super().__str__()} with MMTk"

    def is_oom(self, output: bytes) -> bool:
        return b"Out of Memory!" in output


@register(Runtime)
class JuliaStock(Julia):
    def get_heapsize_modifiers(self, size: int) -> list[Modifier]:
        return []

    def __str__(self):
        return f"{super().__str__()} stock version"

    def is_oom(self, output: bytes) -> bool:
        return False
