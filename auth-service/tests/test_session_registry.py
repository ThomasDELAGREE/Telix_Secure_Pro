import json
import pytest
from unittest.mock import MagicMock, patch
from app.services.session_registry import register_session, revoke_session, SESSION_KEY_PREFIX


def test_register_session_sets_key_with_ttl_and_identity():
    mock_redis = MagicMock()
    with patch("app.services.session_registry.get_redis", return_value=mock_redis):
        register_session("10.0.0.5", "john.doe", "ldap", "aa:bb:cc:dd:ee:ff")
    mock_redis.setex.assert_called_once()
    args, _ = mock_redis.setex.call_args
    assert args[0] == f"{SESSION_KEY_PREFIX}10.0.0.5"
    identity = json.loads(args[2])
    assert identity["user_identifier"] == "john.doe"
    assert identity["identifier_type"] == "ldap"
    assert identity["mac_address"] == "aa:bb:cc:dd:ee:ff"


def test_register_session_ignores_unknown_ip():
    mock_redis = MagicMock()
    with patch("app.services.session_registry.get_redis", return_value=mock_redis):
        register_session("unknown", "john.doe", "ldap")
    mock_redis.setex.assert_not_called()


def test_revoke_session_deletes_key():
    mock_redis = MagicMock()
    with patch("app.services.session_registry.get_redis", return_value=mock_redis):
        revoke_session("10.0.0.5")
    mock_redis.delete.assert_called_once_with(f"{SESSION_KEY_PREFIX}10.0.0.5")
