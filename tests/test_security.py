"""Tests for path validation security."""

import pytest

from app.core.security import SecurityError, validate_path, validate_url, sanitize_filename


def test_validate_existing_path(tmp_path):
    p = tmp_path / "test"
    p.mkdir()
    result = validate_path(str(p), must_exist=True)
    assert result.exists()


def test_path_traversal_blocked():
    with pytest.raises(SecurityError):
        validate_path("C:\\Users\\..\\..\\Windows\\System32")


def test_empty_path_blocked():
    with pytest.raises(SecurityError):
        validate_path("")


def test_validate_url_https():
    assert validate_url("https://github.com") == "https://github.com"


def test_validate_url_localhost():
    url = validate_url("localhost:3000")
    assert url.startswith("http://")


def test_validate_url_domain():
    url = validate_url("github.com")
    assert url == "https://github.com"


def test_sanitize_filename():
    assert sanitize_filename("test<file>.txt") == "testfile.txt"
