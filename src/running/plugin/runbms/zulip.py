from typing import Optional, TYPE_CHECKING
import zulip
from running.plugin.runbms import RunbmsPlugin
from running.util import Moma, register, MomaReservationStatus, config_index_to_chr
import logging
import copy
from running.suite import is_dry_run
from running.command.runbms import hfac_str
from datetime import datetime, timedelta
if TYPE_CHECKING:
    from running.benchmark import Benchmark

RESERVATION_WARNING_HOURS = 12
RESERVATION_WARNING_THRESHOLD = timedelta(
    seconds=RESERVATION_WARNING_HOURS * 60 * 60)


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
        message_data["content"] = "{}\n{}{}\n".format(
            self.run_id,
            self.get_reservation_message(),
            content
        )
        try:
            result = self.client.send_message(message_data=message_data)
            if result["result"] != "success":
                logging.warning("Zulip send_message failed\n{}".format(result))
            else:
                self.last_message_id = result["id"]
                self.last_message_content = message_data["content"]
        except:
            logging.exception("Unhandled Zulip send_message exception")

    def modify_message(self, content):
        request = {
            "message_id": self.last_message_id,
            "content": content,
        }
        try:
            result = self.client.update_message(request)
            if result["result"] != "success":
                logging.warning(
                    "Zulip update_message failed\n{}".format(result))
            else:
                self.last_message_content = content
        except:
            logging.exception("Unhandled Zulip update_message exception")

    def __str__(self) -> str:
        return "Zulip {}".format(self.name)

    def start_hfac(self, hfac: Optional[float]):
        if self.nop:
            return
        self.send_message("hfac {} started".format(
            hfac_str(hfac) if hfac is not None else "None"))

    def end_hfac(self, hfac: Optional[float]):
        if self.nop:
            return
        self.send_message("hfac {} ended".format(
            hfac_str(hfac) if hfac is not None else "None"))

    def start_benchmark(self, _hfac: Optional[float], _size: Optional[int], bm: "Benchmark"):
        if self.nop:
            return
        self.send_message("benchmark {} started".format(bm.name))

    def end_benchmark(self, _hfac: Optional[float], _size: Optional[int], bm: "Benchmark"):
        if self.nop:
            return
        self.send_message("benchmark {} ended".format(bm.name))

    def start_invocation(self, _hfac: Optional[float], _size: Optional[int], _bm: "Benchmark", invocation: int):
        if self.nop:
            return
        if self.last_message_id and self.last_message_content:
            self.modify_message(self.last_message_content + str(invocation))

    def end_invocation(self, _hfac: Optional[float], _size: Optional[int], _bm: "Benchmark", _invocation: int):
        if self.nop:
            return

    def start_config(self, _hfac: Optional[float], _size: Optional[int], _bm: "Benchmark", _invocation: int, _config: str, _config_index: int):
        if self.nop:
            return

    def end_config(self, _hfac: Optional[float], _size: Optional[int], _bm: "Benchmark", _invocation: int, _config: str, config_index: int, passed: bool):
        if self.nop:
            return
        if self.last_message_id and self.last_message_content:
            if passed:
                self.modify_message(self.last_message_content +
                                    config_index_to_chr(config_index))
            else:
                self.modify_message(self.last_message_content + ".")

    def get_reservation_message(self) -> str:
        reservation = self.moma.get_reservation()
        if reservation is None:
            return ""
        if reservation.status is MomaReservationStatus.NOT_MOMA:
            return "# ** Warning: not running on a moma machine. **\n"
        elif reservation.status is MomaReservationStatus.NOT_RESERVED:
            return "# ** Warning: machine not reserved. **\n"
        elif reservation.status is MomaReservationStatus.RESERVED_BY_OTHERS:
            return "# ** Warning: machine reserved by {}, ends at {}. **\n".format(
                reservation.user,
                reservation.end
            )
        elif reservation.status is MomaReservationStatus.RESERVED_BY_ME:
            assert reservation.end is not None
            delta = reservation.end - datetime.now()
            if delta < RESERVATION_WARNING_THRESHOLD:
                return "# ** Warning: less than {} hours of reservation left. Current reservation ends at {}. **\n".format(
                    RESERVATION_WARNING_HOURS,
                    reservation.end
                )
            else:
                return ""
        else:
            raise ValueError("Unhandled reservation status value")
