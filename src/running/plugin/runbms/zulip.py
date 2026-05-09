import copy
import logging
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

import zulip

from running.command.runbms import hfac_str
from running.plugin.runbms import RunbmsPlugin
from running.suite import is_dry_run
from running.util import (
    Moma,
    MomaReservationStatus,
    config_index_to_chr,
    detect_rogue_processes,
    get_logged_in_users,
    register,
    system,
)

if TYPE_CHECKING:
    from running.benchmark import Benchmark

RESERVATION_WARNING_HOURS = 12
RESERVATION_WARNING_THRESHOLD = timedelta(seconds=RESERVATION_WARNING_HOURS * 60 * 60)


@register(RunbmsPlugin)
class Zulip(RunbmsPlugin):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.config_file = kwargs.get("config_file", "~/.zuliprc")
        self.client = zulip.Client(config_file=self.config_file)
        self.request = kwargs.get("request", {})
        if type(self.request) is not dict:
            raise TypeError("request of Zulip must be a dictionary")
        if self.request.get("type") not in ["private", "stream"]:
            raise ValueError("Request type must be either private or stream")
        if self.request.get("type") == "stream" and "topic" not in self.request:
            raise KeyError("Stream messages must have a topic")
        if "to" not in self.request:
            raise KeyError("Request must have a to field")
        self.nop = is_dry_run()
        self.moma = Moma()
        self.last_message_id = None
        self.last_message_content = None

    def send_message(self, content):
        message_data = copy.deepcopy(self.request)
        message_data["content"] = (
            f"{self.run_id}\n"
            f"{self.get_reservation_message()}"
            f"{self.get_user_warnings()}"
            f"{self.get_rogue_process_warnings()}"
            f"{content}\n"
        )
        try:
            result = self.client.send_message(message_data=message_data)
            if result["result"] != "success":
                logging.warning(f"Zulip send_message failed\n{result}")
            else:
                self.last_message_id = result["id"]
                self.last_message_content = message_data["content"]
        except Exception:
            logging.exception("Unhandled Zulip send_message exception")

    def modify_message(self, content):
        request = {
            "message_id": self.last_message_id,
            "content": content,
        }
        try:
            result = self.client.update_message(request)
            if result["result"] != "success":
                logging.warning(f"Zulip update_message failed\n{result}")
            else:
                self.last_message_content = content
        except Exception:
            logging.exception("Unhandled Zulip update_message exception")

    def __str__(self) -> str:
        return f"Zulip {self.name}"

    def start_hfac(self, hfac: float | None):
        if self.nop:
            return
        self.send_message(
            "hfac {} started".format(hfac_str(hfac) if hfac is not None else "None")
        )

    def end_hfac(self, hfac: float | None):
        if self.nop:
            return
        self.send_message(
            "hfac {} ended".format(hfac_str(hfac) if hfac is not None else "None")
        )

    def start_benchmark(self, hfac: float | None, size: int | None, bm: "Benchmark"):
        if self.nop:
            return
        self.send_message(f"benchmark {bm.name} started")

    def end_benchmark(self, hfac: float | None, size: int | None, bm: "Benchmark"):
        if self.nop:
            return
        self.send_message(f"benchmark {bm.name} ended")

    def start_invocation(
        self,
        hfac: float | None,
        size: int | None,
        bm: "Benchmark",
        invocation: int,
    ):
        if self.nop:
            return
        if self.last_message_id and self.last_message_content:
            self.modify_message(self.last_message_content + str(invocation))

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
        if self.last_message_id and self.last_message_content:
            if passed:
                self.modify_message(
                    self.last_message_content + config_index_to_chr(config_index)
                )
            else:
                self.modify_message(self.last_message_content + ".")

    def get_reservation_message(self) -> str:
        reservation = self.moma.get_reservation()
        if reservation is None:
            return ""
        if reservation.status is MomaReservationStatus.NOT_MOMA:
            return ""
        elif reservation.status is MomaReservationStatus.NOT_RESERVED:
            return "# ** Warning: machine not reserved. **\n"
        elif reservation.status is MomaReservationStatus.RESERVED_BY_OTHERS:
            return (
                f"# ** Warning: machine reserved by"
                f" {reservation.user},"
                f" ends at {reservation.end}. **\n"
            )
        elif reservation.status is MomaReservationStatus.RESERVED_BY_ME:
            assert reservation.end is not None
            delta = reservation.end - datetime.now()
            if delta < RESERVATION_WARNING_THRESHOLD:
                return (
                    f"# ** Warning: less than"
                    f" {RESERVATION_WARNING_HOURS}"
                    f" hours of reservation left."
                    f" Current reservation ends"
                    f" at {reservation.end}. **\n"
                )
            else:
                return ""
        else:
            raise ValueError("Unhandled reservation status value")

    def get_user_warnings(self) -> str:
        logged_in_users = get_logged_in_users()
        if len(logged_in_users) > 1:
            return "# ** Warning: more than one user logged in: {}. **\n".format(
                " ".join(sorted(logged_in_users))
            )
        return ""

    def get_rogue_process_warnings(self) -> str:
        """Check for rogue processes with high CPU usage and generate warnings."""
        top_output = system("top -bcn 1 -w512 |head -n 12")
        rogue_processes = detect_rogue_processes(top_output)

        if not rogue_processes:
            return ""

        warning = "# ** Warning: High CPU usage processes detected: **\n"
        for pid, user, cpu_percent, command in rogue_processes:
            warning += (
                f"- Process {command}"
                f" (PID: {pid}, User: {user})"
                f" using {cpu_percent:.1f}% CPU\n"
            )

        return warning
