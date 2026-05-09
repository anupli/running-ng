from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from running.config import Configuration
    from running.modifier import Modifier
    from running.runtime import Runtime
import enum
import getpass
import shlex
import socket
import subprocess
import time
import urllib.request
from datetime import datetime


def system(cmd, check=True) -> str:
    return subprocess.run(
        cmd, check=check, stdout=subprocess.PIPE, shell=True
    ).stdout.decode("utf-8")


def register(parent_class):
    def inner(cls):
        parent_class.CLS_MAPPING[cls.__name__] = cls
        return cls

    return inner


def config_index_to_chr(i: int) -> str:
    if i < 0 or i >= 52:
        raise ValueError(f"Cannot convert {i} into a character")
    elif i < 26:
        return chr(ord("a") + i)
    else:
        return chr(ord("A") + i - 26)


def parse_modifier_strs(
    configuration: "Configuration", mod_strs: list[str]
) -> list["Modifier"]:
    # Some modifiers could be a modifier set, and we need to flatten it
    from running.modifier import ModifierSet

    mods = []
    for m in mod_strs:
        m = m.strip()
        if not m:
            break
        mod_name = m.split("-")[0]
        mod_value_opts = m.split("-")[1:]
        mod = configuration.get("modifiers").get(mod_name)
        if mod is None:
            raise KeyError(f"Modifier '{mod_name}' not defined")
        mod = mod.apply_value_opts(mod_value_opts)
        if isinstance(mod, ModifierSet):
            for m_inner in mod.flatten(configuration):
                mods.append(m_inner)
        else:
            mods.append(mod)
    return mods


def parse_config_str(
    configuration: "Configuration", c: str
) -> tuple["Runtime", list["Modifier"]]:
    runtime = configuration.get("runtimes")[c.split("|")[0].strip()]
    mods = parse_modifier_strs(configuration, c.split("|")[1:])
    return runtime, mods


def dont_emit_heapsize_modifier(configuration: "Configuration", c: str) -> bool:
    mods = parse_modifier_strs(configuration, c.split("|")[1:])
    from running.modifier import NoImplicitHeapsizeModifier

    for mod in mods:
        if isinstance(mod, NoImplicitHeapsizeModifier):
            return True
    return False


def config_str_encode(c: str) -> str:
    return ".".join([x.strip() for x in c.split("|")])


def split_quoted(s: str) -> list[str]:
    return shlex.split(s)


def smart_quote(_s: Any) -> str:
    s = str(_s)
    if s == "":
        return '""'
    need_quote = False
    for c in s:
        if not (c.isalnum() or c in ".:/+=-_"):
            need_quote = True
            break
    if need_quote:
        return f'"{s}"'
    else:
        return s


def get_logged_in_users() -> set[str]:
    output = system("who")
    return set([user_line.split()[0] for user_line in output.splitlines()])


class MomaReservationStatus(enum.Enum):
    NOT_RESERVED = 1
    RESERVED_BY_OTHERS = 2
    RESERVED_BY_ME = 3
    NOT_MOMA = 4


class MomaReservaton:
    def __init__(
        self,
        status: MomaReservationStatus,
        user: str | None,
        start: datetime | None,
        end: datetime | None,
    ):
        self.status = status
        self.user = user
        self.start = start
        self.end = end


class Moma:
    def __init__(self, host: str | None = None, frequency: int = 60):
        if host is None:
            self.host = system("hostname -s").strip()
            self.is_moma = system("hostname -d").strip() == "moma"
        else:
            self.host = host
            try:
                self.is_moma = socket.gethostbyname_ex(self.host)[0].endswith(".moma")
            except socket.gaierror:
                self.is_moma = False
        self.reserve_time_url = f"http://10.0.0.1/reserve-time?host={self.host}"
        self.frequency = frequency
        self.last_checked: float | None
        self.last_checked = None
        self.reservation: MomaReservaton | None
        self.reservation = None
        self.update_reservation()

    def update_reservation(self):
        now = time.time()
        if self.last_checked:
            if now - self.last_checked <= self.frequency:
                return
        if not self.is_moma:
            self.reservation = MomaReservaton(
                MomaReservationStatus.NOT_MOMA, None, None, None
            )
        else:
            with urllib.request.urlopen(self.reserve_time_url) as response:
                html = response.read()
                if not html:
                    self.reservation = MomaReservaton(
                        MomaReservationStatus.NOT_RESERVED, None, None, None
                    )
                else:
                    html = html.decode("utf-8")
                    user, start, end = html.split(",")
                    status = (
                        MomaReservationStatus.RESERVED_BY_ME
                        if user == getpass.getuser()
                        else MomaReservationStatus.RESERVED_BY_OTHERS
                    )
                    start = datetime.fromtimestamp(int(start))
                    end = datetime.fromtimestamp(int(end))
                    self.reservation = MomaReservaton(status, user, start, end)
        self.last_checked = now

    def get_reservation(self) -> MomaReservaton | None:
        self.update_reservation()
        return self.reservation


def detect_rogue_processes(
    top_output: str, cpu_threshold: float = 50.0
) -> list[tuple[str, str, float, str]]:
    """
    Parse top output and detect processes with high CPU usage.

    Args:
        top_output: Raw output from top command
        cpu_threshold: CPU percentage threshold for considering a process "rogue"

    Returns:
        List of tuples: (pid, user, cpu_percent, command)
    """
    rogue_processes: list[tuple[str, str, float, str]] = []
    lines = top_output.splitlines()

    # Find the start of the process list (after the header line with PID USER PR NI...)
    process_start_idx = -1
    for i, line in enumerate(lines):
        if line.strip().startswith("PID") and "USER" in line and "%CPU" in line:
            process_start_idx = i + 1
            break

    if process_start_idx == -1:
        return rogue_processes

    # Parse each process line
    for line in lines[process_start_idx:]:
        if not line.strip():
            continue

        # Split the line and extract relevant fields
        # Format: PID USER PR NI VIRT RES SHR S %CPU %MEM TIME+ COMMAND
        parts = line.split()
        if len(parts) < 12:
            continue

        try:
            pid = parts[0]
            user = parts[1]
            cpu_percent = float(parts[8])  # %CPU column
            command = " ".join(parts[11:])  # COMMAND column (may contain spaces)

            if cpu_percent >= cpu_threshold:
                rogue_processes.append((pid, user, cpu_percent, command))
        except (ValueError, IndexError):
            # Skip lines that don't match expected format
            continue

    return rogue_processes
