"""Cryptographic helpers: Argon2id hashing, tokens, HMACs, secret encryption, pre-login CSRF."""
import hashlib
import hmac
import secrets
from functools import lru_cache

from argon2 import PasswordHasher, Type
from argon2.exceptions import InvalidHashError, VerificationError
from cryptography.fernet import Fernet

from app.core.config import get_settings


@lru_cache
def _hasher() -> PasswordHasher:
    s = get_settings()
    return PasswordHasher(
        time_cost=s.argon2_time_cost,
        memory_cost=s.argon2_memory_cost_kib,
        parallelism=s.argon2_parallelism,
        type=Type.ID,
    )


def hash_password(password: str) -> str:
    return _hasher().hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    try:
        return _hasher().verify(password_hash, password)
    except (VerificationError, InvalidHashError):
        return False


def password_needs_rehash(password_hash: str) -> bool:
    return _hasher().check_needs_rehash(password_hash)


@lru_cache
def dummy_hash() -> str:
    """Verified against when the username does not exist, to keep login timing uniform."""
    return hash_password("dummy-password-for-timing-equalisation")


def new_token() -> str:
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    """Session tokens are high-entropy, so a plain SHA-256 is sufficient for storage."""
    return hashlib.sha256(token.encode()).hexdigest()


def ct_eq(a: str, b: str) -> bool:
    return hmac.compare_digest(a.encode(), b.encode())


def keyed_hash(value: str, purpose: str) -> str:
    key = get_settings().session_secret.get_secret_value().encode()
    return hmac.new(key, f"{purpose}:{value}".encode(), hashlib.sha256).hexdigest()


@lru_cache
def _fernet() -> Fernet:
    return Fernet(get_settings().totp_encryption_key.get_secret_value().encode())


def encrypt_secret(plaintext: str) -> str:
    return _fernet().encrypt(plaintext.encode()).decode()


def decrypt_secret(token: str) -> str:
    return _fernet().decrypt(token.encode()).decode()


# --- Pre-login CSRF (double-submit cookie, HMAC-signed) ------------------------------------
def new_anon_csrf() -> tuple[str, str]:
    """Returns (form_token, cookie_value)."""
    token = new_token()
    return token, f"{token}.{keyed_hash(token, 'anon-csrf')}"


def verify_anon_csrf(form_token: str, cookie_value: str) -> bool:
    if not form_token or not cookie_value or "." not in cookie_value:
        return False
    token, _, sig = cookie_value.partition(".")
    return ct_eq(sig, keyed_hash(token, "anon-csrf")) and ct_eq(token, form_token)
