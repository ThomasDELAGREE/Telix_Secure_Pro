import pytest

from app.services.wireguard_service import allocate_ip, IpPoolExhausted


def test_allocate_ip_returns_first_free_address():
    ip = allocate_ip("10.200.0.0/24", already_allocated=set())
    assert ip == "10.200.0.1"


def test_allocate_ip_skips_already_allocated():
    ip = allocate_ip("10.200.0.0/30", already_allocated={"10.200.0.1"})
    assert ip == "10.200.0.2"


def test_allocate_ip_raises_when_pool_exhausted():
    # /30 -> seulement 2 adresses hote utilisables (10.200.0.1 et .2)
    with pytest.raises(IpPoolExhausted):
        allocate_ip("10.200.0.0/30", already_allocated={"10.200.0.1", "10.200.0.2"})
