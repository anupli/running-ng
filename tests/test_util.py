from pathlib import Path
from running.config import Configuration
from running.util import parse_config_str, smart_quote, split_quoted


def test_split_quoted():
    assert split_quoted("123 \"foo bar\"") == ["123", "foo bar"]


def test_smart_quote():
    assert smart_quote(Path("/bin")/"123 456") == "\"/bin/123 456\""


def test_issue104():
    c = Configuration({
        "suites": {
            "dacapo2006": {
                "type": "DaCapo",
                "release": "2006",
                "path": "/usr/share/benchmarks/dacapo/dacapo-2006-10-MR2.jar",
                "timing_iteration": 3
            }
        },
        "benchmarks": {
            "dacapo2006": [
                "fop"
            ]
        },
        "runtimes": {
            "jdk8": {
                "type": "OpenJDK",
                "release": 8,
                "home": "/usr/lib/jvm/temurin-8-jdk-amd64"
            }
        },
        "modifiers": {}
    })
    c.resolve_class()
    _, modifiers = parse_config_str(c, "jdk8|")
    assert len(modifiers) == 0
