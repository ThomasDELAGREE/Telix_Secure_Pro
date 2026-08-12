import base64

from agent.enrollment import generate_local_keypair


def test_generate_local_keypair_returns_distinct_base64_keys():
    priv, pub = generate_local_keypair()
    assert priv != pub
    assert len(base64.b64decode(priv)) == 32
    assert len(base64.b64decode(pub)) == 32


def test_generate_local_keypair_is_random_each_call():
    priv1, _ = generate_local_keypair()
    priv2, _ = generate_local_keypair()
    assert priv1 != priv2
