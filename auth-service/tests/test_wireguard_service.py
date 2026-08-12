import pytest

from app.services.wireguard_service import allocate_ip, generate_keypair, IpPoolExhausted


def test_generate_keypair_returns_distinct_base64_keys():
    priv, pub = generate_keypair()
    assert priv != pub
    assert len(priv) > 0 and len(pub) > 0
    # Les cles WireGuard/X25519 brutes font 32 octets -> 44 caracteres en base64 (avec padding)
    import base64

    assert len(base64.b64decode(priv)) == 32
    assert len(base64.b64decode(pub)) == 32


def test_generate_keypair_is_random_each_call():
    priv1, _ = generate_keypair()
    priv2, _ = generate_keypair()
    assert priv1 != priv2


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
