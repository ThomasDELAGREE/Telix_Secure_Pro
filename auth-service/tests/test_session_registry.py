import pytest
from unittest.mock import MagicMock, patch
from app.services.session_registry import register_session, revoke_session, SESSION_KEY_PREFIX


def test_register_session_sets_key_with_ttl():
    mock_redis = MagicMock()
    with patch("app.services.session_registry.get_redis", return_value=mock_redis):
        register_session("10.0.0.5", "john.doe")
    mock_redis.setex.assert_called_once()
    args, _ = mock_redis.setex.call_args
    assert args[0] == f"{SESSION_KEY_PREFIX}10.0.0.5"
    assert args[2] == "john.doe"


def test_register_session_ignores_unknown_ip():
    mock_redis = MagicMock()
    with patch("app.services.session_registry.get_redis", return_value=mock_redis):
        register_session("unknown", "john.doe")
    mock_redis.setex.assert_not_called()


def test_revoke_session_deletes_key():
    mock_redis = MagicMock()
    with patch("app.services.session_registry.get_redis", return_value=mock_redis):
        revoke_session("10.0.0.5")
    mock_redis.delete.assert_called_once_with(f"{SESSION_KEY_PREFIX}10.0.0.5")
