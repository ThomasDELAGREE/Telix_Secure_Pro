import pytest
from unittest.mock import MagicMock, patch
from app.services.otp_service import OTPService


@pytest.fixture
def svc():
    return OTPService()


def test_normalize_phone_valid(svc):
    assert svc._normalize_phone("+33612345678") == "+33612345678"


def test_normalize_phone_invalid(svc):
    with pytest.raises(ValueError):
        svc._normalize_phone("not-a-phone")


def test_generate_otp_length(svc):
    otp = svc._generate_otp()
    from app.core.config import settings
    assert len(otp) == settings.OTP_LENGTH
    assert otp.isdigit()


def test_verify_otp_success(svc):
    mock_redis = MagicMock()
    mock_redis.get.return_value = "123456"
    with patch("app.services.otp_service.get_redis", return_value=mock_redis):
        result = svc.verify_otp("+33612345678", "123456")
    assert result is True
    mock_redis.delete.assert_called_once()


def test_verify_otp_wrong_code(svc):
    mock_redis = MagicMock()
    mock_redis.get.return_value = "123456"
    with patch("app.services.otp_service.get_redis", return_value=mock_redis):
        result = svc.verify_otp("+33612345678", "999999")
    assert result is False


def test_verify_otp_expired(svc):
    mock_redis = MagicMock()
    mock_redis.get.return_value = None
    with patch("app.services.otp_service.get_redis", return_value=mock_redis):
        result = svc.verify_otp("+33612345678", "123456")
    assert result is False
