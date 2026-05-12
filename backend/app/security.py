import base64
import hashlib
import hmac
import json
import secrets
import time
from typing import Any


def hash_password(password: str, *, salt: str | None = None) -> tuple[str, str]:
    actual_salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), actual_salt.encode("utf-8"), 120_000)
    return actual_salt, digest.hex()


def verify_password(password: str, salt: str, expected_hash: str) -> bool:
    _, computed_hash = hash_password(password, salt=salt)
    return hmac.compare_digest(computed_hash, expected_hash)


def create_token(subject: str, secret: str, *, expires_in_hours: int) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {"sub": subject, "iat": int(time.time()), "exp": int(time.time()) + expires_in_hours * 3600}
    header_b64 = _b64url(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    payload_b64 = _b64url(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signature = _sign(f"{header_b64}.{payload_b64}".encode("utf-8"), secret)
    return f"{header_b64}.{payload_b64}.{signature}"


def decode_token(token: str, secret: str) -> dict[str, Any]:
    try:
        header_b64, payload_b64, signature = token.split(".")
    except ValueError as exc:
        raise ValueError("invalid token format") from exc

    expected_signature = _sign(f"{header_b64}.{payload_b64}".encode("utf-8"), secret)
    if not hmac.compare_digest(signature, expected_signature):
        raise ValueError("invalid token signature")

    payload = json.loads(_b64url_decode(payload_b64).decode("utf-8"))
    if payload.get("exp", 0) < int(time.time()):
        raise ValueError("token expired")
    return payload


def _sign(value: bytes, secret: str) -> str:
    return _b64url(hmac.new(secret.encode("utf-8"), value, hashlib.sha256).digest())


def _b64url(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("utf-8").rstrip("=")


def _b64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(f"{value}{padding}")
