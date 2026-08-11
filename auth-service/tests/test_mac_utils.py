import pytest
from app.core.mac_utils import normalize_mac


@pytest.mark.parametrize("raw,expected", [
    ("AA:BB:CC:DD:EE:FF", "aa:bb:cc:dd:ee:ff"),
    ("aa-bb-cc-dd-ee-ff", "aa:bb:cc:dd:ee:ff"),
    ("AABBCCDDEEFF", "aa:bb:cc:dd:ee:ff"),
    ("aa.bb.cc.dd.ee.ff", "aa:bb:cc:dd:ee:ff"),
])
def test_normalize_mac_valid(raw, expected):
    assert normalize_mac(raw) == expected


@pytest.mark.parametrize("raw", ["not-a-mac", "AA:BB:CC", "", None])
def test_normalize_mac_invalid(raw):
    assert normalize_mac(raw) is None
