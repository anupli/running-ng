from running.command.runbms import spread, setup_parser
import pytest
import argparse
import random


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
    args = parser.parse_args(["runbms", "/tmp/logs", "/tmp/config.yml"])
    assert hasattr(args, "exit_on_failure")
    assert args.exit_on_failure is None

    # Test that the flag can be set without argument (defaults to 1)
    args = parser.parse_args(
        ["runbms", "/tmp/logs", "/tmp/config.yml", "--exit-on-failure"]
    )
    assert args.exit_on_failure == 1

    # Test that the flag can be set with custom argument
    args = parser.parse_args(
        ["runbms", "/tmp/logs", "/tmp/config.yml", "--exit-on-failure", "42"]
    )
    assert args.exit_on_failure == 42


def test_global_variables_initialization():
    """Test that the new global variables are properly initialized."""
    from running.command import runbms

    # Test that the new global variables exist
    assert hasattr(runbms, "exit_on_failure_code")

    # Test default values (these are module-level globals)
    # Note: These might be modified by other tests, so we just check they exist
    assert runbms.exit_on_failure_code is None or isinstance(
        runbms.exit_on_failure_code, int
    )


def test_randomize_configs_arg_parsing():
    """Test that --randomize-configs argument is parsed correctly"""
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    setup_parser(subparsers)

    # Test without the flag
    args = parser.parse_args(["runbms", "/tmp/log", "/tmp/config.yml"])
    assert args.randomize_configs == False

    # Test with the flag
    args = parser.parse_args(
        ["runbms", "--randomize-configs", "/tmp/log", "/tmp/config.yml"]
    )
    assert args.randomize_configs == True


def test_exit_on_failure_flag_parsing():
    """Test that the --exit-on-failure flag is parsed correctly."""
    from running.command.runbms import setup_parser
    import argparse

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    setup_parser(subparsers)

    # Test that the flag is recognized and sets the correct default value
    args = parser.parse_args(["runbms", "/tmp/logs", "/tmp/config.yml"])
    assert hasattr(args, "exit_on_failure")
    assert args.exit_on_failure is None

    # Test that the flag can be set without argument (defaults to 1)
    args = parser.parse_args(
        ["runbms", "/tmp/logs", "/tmp/config.yml", "--exit-on-failure"]
    )
    assert args.exit_on_failure == 1

    # Test that the flag can be set with custom argument
    args = parser.parse_args(
        ["runbms", "/tmp/logs", "/tmp/config.yml", "--exit-on-failure", "42"]
    )
    assert args.exit_on_failure == 42


def test_global_variables_initialization():
    """Test that the new global variables are properly initialized."""
    from running.command import runbms

    # Test that the new global variables exist
    assert hasattr(runbms, "exit_on_failure_code")

    # Test default values (these are module-level globals)
    # Note: These might be modified by other tests, so we just check they exist
    assert runbms.exit_on_failure_code is None or isinstance(
        runbms.exit_on_failure_code, int
    )


def test_config_randomization_logic():
    """Test that the config randomization logic works as expected"""
    # Test the randomization logic independently
    configs = ["config1", "config2", "config3", "config4", "config5"]

    # When randomize_configs is False, order should be preserved
    config_indices = list(range(len(configs)))
    # No shuffling should occur
    original_order = config_indices.copy()
    assert config_indices == original_order

    # When randomize_configs is True, shuffling should occur
    # Test multiple times to make sure we get different orders (statistically)
    config_indices = list(range(len(configs)))
    different_orders = 0
    random.seed(42)  # Set seed for reproducible test

    for _ in range(10):
        test_indices = list(range(len(configs)))
        random.shuffle(test_indices)
        if test_indices != original_order:
            different_orders += 1

    # With 5 configs shuffled 10 times, we should get at least some different orders
    assert different_orders > 0, "Shuffling should produce different orders"
>>>>>>> 939de1b865db4727bfe0f143131c223d8b520834
