"""Unit tests for app.utils.crypto."""

from app.utils.crypto import generate_webhook_key, hash_key, key_prefix, verify_key


class TestGenerateWebhookKey:
    def test_prefix(self):
        key = generate_webhook_key()
        assert key.startswith("fsk_")

    def test_length(self):
        key = generate_webhook_key()
        # "fsk_" + 32 bytes base64url ≈ 43 chars → total ~47
        assert len(key) > 40

    def test_uniqueness(self):
        keys = {generate_webhook_key() for _ in range(20)}
        assert len(keys) == 20


class TestHashKey:
    def test_deterministic(self):
        key = "fsk_test123"
        assert hash_key(key) == hash_key(key)

    def test_hex_string(self):
        h = hash_key("fsk_test123")
        assert len(h) == 64  # SHA-256 hex digest
        assert all(c in "0123456789abcdef" for c in h)

    def test_different_keys_different_hashes(self):
        assert hash_key("key_a") != hash_key("key_b")


class TestKeyPrefix:
    def test_returns_first_8_chars(self):
        assert key_prefix("fsk_abcdefgh_rest") == "fsk_abcd"

    def test_short_key(self):
        assert key_prefix("abc") == "abc"


class TestVerifyKey:
    def test_correct_key(self):
        key = generate_webhook_key()
        stored = hash_key(key)
        assert verify_key(key, stored) is True

    def test_incorrect_key(self):
        key = generate_webhook_key()
        stored = hash_key(key)
        assert verify_key("wrong_key", stored) is False

    def test_tampered_hash(self):
        key = generate_webhook_key()
        assert verify_key(key, "0" * 64) is False
