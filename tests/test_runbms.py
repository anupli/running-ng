from running.command.runbms import spread, setup_parser
import pytest
import argparse


def test_spread_0():
    spread_factor = 0
    N = 8
    for i in range(0, N + 1):
        assert spread(spread_factor, N, i) == i


def test_spread_1():
    spread_factor = 1
    N = 8
    for i in range(1, N + 1):
        left = pytest.approx(
            spread(spread_factor, N, i) - spread(spread_factor, N, i - 1)
        )
        right = pytest.approx(1 + (i - 1) / 7)
        assert left == right


def test_randomize_configs_arg_parsing():
    """Test that --randomize-configs argument is parsed correctly"""
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    setup_parser(subparsers)
    
    # Test without the flag
    args = parser.parse_args(['runbms', '/tmp/log', '/tmp/config.yml'])
    assert args.randomize_configs == False
    
    # Test with the flag
    args = parser.parse_args(['runbms', '--randomize-configs', '/tmp/log', '/tmp/config.yml'])
    assert args.randomize_configs == True
