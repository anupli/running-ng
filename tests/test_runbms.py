from running.command.runbms import spread
import pytest


def test_spread_0():
    spread_factor = 0
    N = 8
    for i in range(0, N + 1):
        assert spread(spread_factor, N, i) == i


def test_spread_1():
    spread_factor = 1
    N = 8
    for i in range(1, N + 1):
        left = pytest.approx(spread(spread_factor, N, i) -
                             spread(spread_factor, N, i - 1))
        right = pytest.approx(1 + (i-1) / 7)
        assert left == right
