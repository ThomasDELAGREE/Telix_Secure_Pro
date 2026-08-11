import pytest
from unittest.mock import MagicMock
from app.services.room_service import RoomService
from datetime import datetime, timezone, timedelta


class FakeRoom:
    def __init__(self, room_number, access_code, active=True, valid_from=None, valid_until=None):
        self.room_number = room_number
        self.access_code = access_code
        self.active = active
        self.valid_from = valid_from
        self.valid_until = valid_until


@pytest.fixture
def svc():
    return RoomService()


def _db_with(room):
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = room
    return db


def test_authenticate_success(svc):
    room = FakeRoom("101", "secret123")
    assert svc.authenticate(_db_with(room), "101", "secret123") is True


def test_authenticate_wrong_code(svc):
    room = FakeRoom("101", "secret123")
    assert svc.authenticate(_db_with(room), "101", "wrong") is False


def test_authenticate_room_not_found(svc):
    assert svc.authenticate(_db_with(None), "999", "secret123") is False


def test_authenticate_inactive_room(svc):
    room = FakeRoom("101", "secret123", active=False)
    assert svc.authenticate(_db_with(room), "101", "secret123") is False


def test_authenticate_expired_room(svc):
    room = FakeRoom("101", "secret123", valid_until=datetime.now(timezone.utc) - timedelta(days=1))
    assert svc.authenticate(_db_with(room), "101", "secret123") is False
