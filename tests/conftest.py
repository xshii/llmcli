"""
Pytest configuration and fixtures
"""

import os

import pytest


def pytest_configure(config):
    """Register custom markers"""
    config.addinivalue_line("markers", "network: mark test as requiring network access")
    config.addinivalue_line("markers", "slow: mark test as slow running")
    config.addinivalue_line("markers", "integration: mark test as integration test")
    config.addinivalue_line(
        "markers", "requires_api_key: mark test as requiring API key"
    )


def pytest_collection_modifyitems(config, items):
    """
    Automatically skip network tests if SKIP_NETWORK_TESTS is set
    """
    skip_network = os.environ.get("SKIP_NETWORK_TESTS", "false").lower() == "true"

    if skip_network:
        skip_marker = pytest.mark.skip(
            reason="Network tests skipped (SKIP_NETWORK_TESTS=true)"
        )
        for item in items:
            # Skip tests in test_token_manager.py as they require network
            if "test_token_manager" in item.nodeid:
                item.add_marker(skip_marker)
            # Or if explicitly marked as network test
            if "network" in item.keywords:
                item.add_marker(skip_marker)


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Setup test environment"""
    # Set environment variables for testing
    os.environ["AICODE_DB_PATH"] = ":memory:"  # Use in-memory database for tests
    yield
    # Cleanup after all tests
