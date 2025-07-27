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
        left = pytest.approx(
            spread(spread_factor, N, i) - spread(spread_factor, N, i - 1)
        )
        right = pytest.approx(1 + (i - 1) / 7)
        assert left == right


def test_exit_on_failure_flag_available():
    """Test that the --exit-on-failure flag is available in the argument parser."""
    from running.command.runbms import setup_parser
    import argparse
    
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    setup_parser(subparsers)
    
    # Test that the flag is recognized and sets the correct default value
    args = parser.parse_args(['runbms', '/tmp/logs', '/tmp/config.yml'])
    assert hasattr(args, 'exit_on_failure')
    assert args.exit_on_failure is False
    
    # Test that the flag can be set
    args = parser.parse_args(['runbms', '--exit-on-failure', '/tmp/logs', '/tmp/config.yml'])
    assert args.exit_on_failure is True


def test_global_variables_initialization():
    """Test that the new global variables are properly initialized."""
    from running.command import runbms
    
    # Test that the new global variables exist
    assert hasattr(runbms, 'exit_on_failure')
    assert hasattr(runbms, 'any_config_failed')
    
    # Test default values (these are module-level globals)
    # Note: These might be modified by other tests, so we just check they exist
    assert isinstance(runbms.exit_on_failure, bool)
    assert isinstance(runbms.any_config_failed, bool)
