from typing import Optional, TYPE_CHECKING
import zulip
from running.plugin.runbms import RunbmsPlugin
from running.util import register
import logging
import copy
from running.suite import is_dry_run
from running.command.runbms import hfac_str
if TYPE_CHECKING:
    from running.benchmark import Benchmark


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

    def send_message(self, content):
        message_data = copy.deepcopy(self.request)
        message_data["content"] = "{}\n{}".format(self.run_id, content)
        try:
            result = self.client.send_message(message_data=message_data)
            if result["result"] != "success":
                logging.warning("Zulip send_message failed\n{}".format(result))
        except:
            logging.exception("Unhandled Zulip send_message exception")

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

    def start_benchmark(self, _hfac: Optional[float], bm: "Benchmark"):
        if self.nop:
            return
        self.send_message("benchmark {} started".format(bm.name))

    def end_benchmark(self, _hfac: Optional[float], bm: "Benchmark"):
        if self.nop:
            return
        self.send_message("benchmark {} ended".format(bm.name))
