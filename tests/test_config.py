#!/usr/bin/env python3
"""Test configuration module."""

from dashboard.config import Config, DevelopmentConfig, ProductionConfig, TestingConfig


def test_config_classes():
    """Test that config classes have expected attributes."""
    # Base config
    assert Config.SECRET_KEY
    assert Config.PROJECT_ROOT
    assert Config.BUILD_DIR

    # Development config
    assert DevelopmentConfig.DEBUG is True
    assert DevelopmentConfig.TESTING is False

    # Testing config
    assert TestingConfig.DEBUG is True
    assert TestingConfig.TESTING is True

    # Production config
    assert ProductionConfig.DEBUG is False
    assert ProductionConfig.TESTING is False


def test_get_config():
    """Test get_config function."""
    from dashboard.config import get_config

    # Default should be development
    config = get_config()
    assert config.DEBUG is True

    # Test specific configs
    config = get_config("testing")
    assert config.TESTING is True

    config = get_config("production")
    assert config.DEBUG is False
