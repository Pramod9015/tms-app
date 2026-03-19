"""
Tests for JWT token creation and verification.
"""
import pytest
from app.security.jwt_handler import create_access_token, create_refresh_token, decode_token
from fastapi import HTTPException


def test_access_token_valid():
    token = create_access_token({"sub": "1", "role": "user"})
    payload = decode_token(token, "access")
    assert payload["sub"] == "1"
    assert payload["role"] == "user"


def test_refresh_token_valid():
    token = create_refresh_token({"sub": "1", "role": "admin"})
    payload = decode_token(token, "refresh")
    assert payload["sub"] == "1"


def test_wrong_token_type_raises():
    access = create_access_token({"sub": "1"})
    with pytest.raises(HTTPException) as exc_info:
        decode_token(access, "refresh")
    assert exc_info.value.status_code == 401


def test_invalid_token_raises():
    with pytest.raises(HTTPException):
        decode_token("not.a.valid.token", "access")
