import pytest
from jose import JWTError
from app.core.security import create_access_token, decode_access_token


def test_create_and_decode_token():
    token = create_access_token(subject="john.doe", extra_claims={"auth_type": "ldap"})
    payload = decode_access_token(token)
    assert payload["sub"] == "john.doe"
    assert payload["auth_type"] == "ldap"


def test_invalid_token_raises():
    with pytest.raises(JWTError):
        decode_access_token("not.a.valid.token")
