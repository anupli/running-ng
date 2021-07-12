from pathlib import Path
from running.util import smart_quote, split_quoted


def test_split_quoted():
    assert split_quoted("123 \"foo bar\"") == ["123", "foo bar"]


def test_smart_quote():
    assert smart_quote(Path("/bin")/"123 456") == "\"/bin/123 456\""
