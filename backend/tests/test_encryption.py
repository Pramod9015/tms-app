"""
Tests for AES-256 encryption round-trip.
"""
import pytest
from app.security.encryption import encrypt_field, decrypt_field, encrypt_aes256_gcm, decrypt_aes256_gcm


def test_fernet_encrypt_decrypt():
    original = "Test Customer Name #1"
    encrypted = encrypt_field(original)
    assert encrypted != original
    assert decrypt_field(encrypted) == original


def test_fernet_none():
    assert encrypt_field(None) is None
    assert decrypt_field(None) is None


def test_fernet_empty_string():
    encrypted = encrypt_field("")
    assert decrypt_field(encrypted) == ""


def test_aes256_gcm_round_trip():
    msg = "Sensitive beneficiary data: Raj Kumar, +91-9876543210"
    token = encrypt_aes256_gcm(msg)
    assert token != msg
    assert decrypt_aes256_gcm(token) == msg


def test_different_inputs_different_ciphertext():
    e1 = encrypt_field("Alice")
    e2 = encrypt_field("Bob")
    assert e1 != e2
