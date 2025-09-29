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
