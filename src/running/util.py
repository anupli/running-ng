from typing import Any, List, TYPE_CHECKING, Optional, Tuple, Set
if TYPE_CHECKING:
    from running.config import Configuration
    from running.modifier import Modifier
    from running.runtime import Runtime
import shlex
import socket
import urllib.request
import enum
import getpass
from datetime import datetime
import subprocess
import time


def system(cmd, check=True) -> str:
    return subprocess.run(cmd, check=check, stdout=subprocess.PIPE, shell=True).stdout.decode("utf-8")


def register(parent_class):
    def inner(cls):
        parent_class.CLS_MAPPING[cls.__name__] = cls
        return cls
    return inner


def config_index_to_chr(i: int) -> str:
    if i < 0 or i >= 52:
        raise ValueError("Cannot convert {} into a character".format(i))
    elif i < 26:
        return chr(ord('a')+i)
    else:
        return chr(ord('A')+i-26)


def parse_modifier_strs(configuration: 'Configuration', mod_strs: List[str]) -> List['Modifier']:
    # Some modifiers could be a modifier set, and we need to flatten it
    from running.modifier import ModifierSet
    mods = []
    for m in mod_strs:
        m = m.strip()
        mod_name = m.split("-")[0]
        mod_value_opts = m.split("-")[1:]
        mod = configuration.get("modifiers").get(mod_name)
        if mod is None:
            raise KeyError("Modifier '{}' not defined".format(mod_name))
        mod = mod.apply_value_opts(mod_value_opts)
        if isinstance(mod, ModifierSet):
            for m_inner in mod.flatten(configuration):
                mods.append(m_inner)
        else:
            mods.append(mod)
    return mods


def parse_config_str(configuration: 'Configuration', c: str) -> Tuple['Runtime', List['Modifier']]:
    runtime = configuration.get("runtimes")[c.split('|')[0].strip()]
    mods = parse_modifier_strs(configuration, c.split('|')[1:])
    return runtime, mods


def config_str_encode(c: str) -> str:
    return ".".join([x.strip() for x in c.split("|")])


def split_quoted(s: str) -> List[str]:
    return shlex.split(s)


def smart_quote(_s: Any) -> str:
    s = str(_s)
    if s == "":
        return "\"\""
    need_quote = False
    for c in s:
        if not (c.isalnum() or c in '.:/+=-_'):
            need_quote = True
            break
    if need_quote:
        return "\"{}\"".format(s)
    else:
        return s


def get_logged_in_users() -> Set[str]:
    output = system("who")
    return set([l.split()[0] for l in output.splitlines()])


class MomaReservationStatus(enum.Enum):
    NOT_RESERVED = 1
    RESERVED_BY_OTHERS = 2
    RESERVED_BY_ME = 3
    NOT_MOMA = 4


class MomaReservaton(object):
    def __init__(self, status: MomaReservationStatus, user: Optional[str], start: Optional[datetime], end: Optional[datetime]):
        self.status = status
        self.user = user
        self.start = start
        self.end = end


class Moma(object):
    def __init__(self, host: Optional[str] = None, frequency: int = 60):
        if host is None:
            self.host = system("hostname -s").strip()
            self.is_moma = system("hostname -d").strip() == "moma"
        else:
            self.host = host
            try:
                self.is_moma = socket.gethostbyname_ex(
                    self.host)[0].endswith(".moma")
            except socket.gaierror:
                self.is_moma = False
        self.reserve_time_url = "http://10.0.0.1/reserve-time?host={}".format(
            self.host)
        self.frequency = frequency
        self.last_checked: Optional[float]
        self.last_checked = None
        self.reservation: Optional[MomaReservaton]
        self.reservation = None
        self.update_reservation()

    def update_reservation(self):
        now = time.time()
        if self.last_checked:
            if now - self.last_checked <= self.frequency:
                return
        if not self.is_moma:
            self.reservation = MomaReservaton(
                MomaReservationStatus.NOT_MOMA,
                None, None, None
            )
        else:
            with urllib.request.urlopen(self.reserve_time_url) as response:
                html = response.read()
                if not html:
                    self.reservation = MomaReservaton(
                        MomaReservationStatus.NOT_RESERVED,
                        None, None, None
                    )
                else:
                    html = html.decode("utf-8")
                    user, start, end = html.split(",")
                    status = MomaReservationStatus.RESERVED_BY_ME if user == getpass.getuser(
                    ) else MomaReservationStatus.RESERVED_BY_OTHERS
                    start = datetime.fromtimestamp(int(start))
                    end = datetime.fromtimestamp(int(end))
                    self.reservation = MomaReservaton(status, user, start, end)
        self.last_checked = now

    def get_reservation(self) -> Optional[MomaReservaton]:
        self.update_reservation()
        return self.reservation
