"""Webhook key generation and verification utilities."""

import hashlib
import hmac
import secrets


def generate_webhook_key() -> str:
    """Generate a random webhook API key."""
    return "fsk_" + secrets.token_urlsafe(32)


def hash_key(key: str) -> str:
    """SHA-256 hash a key for storage."""
    return hashlib.sha256(key.encode()).hexdigest()


def key_prefix(key: str) -> str:
    """Extract the first 8 characters as a prefix for display."""
    return key[:8]


def verify_key(key: str, stored_hash: str) -> bool:
    """Constant-time comparison of a key against a stored hash."""
    candidate = hash_key(key)
    return hmac.compare_digest(candidate, stored_hash)
