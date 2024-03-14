"""Conftest for pytest tests."""
import pytest
import requests_mock


@pytest.fixture
def fixture_mock_requests():
    """Return started up requests_mock and cleanup on teardown."""
    mock_requests = requests_mock.Mocker(real_http=True)
    mock_requests.start()
    yield mock_requests

    mock_requests.stop()
