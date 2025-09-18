"""Database-related utility helpers."""

from __future__ import annotations

from urllib.parse import quote, urlparse, urlunparse


def _needs_encoding(value: str) -> bool:
    return "%" not in value


def _encode_userinfo_component(value: str | None) -> str:
    if not value:
        return ""
    return quote(value, safe="") if _needs_encoding(value) else value


def normalize_database_url(url: str) -> str:
    """Return a connection URL with safely encoded credentials."""
    if not url:
        raise ValueError("Database URL cannot be empty.")

    parsed = urlparse(url)
    if "@" not in parsed.netloc or not parsed.scheme.startswith("postgres"):
        return url

    userinfo, hostinfo = parsed.netloc.split("@", 1)
    if ":" in userinfo:
        username, password = userinfo.split(":", 1)
    else:
        username, password = userinfo, ""

    username_enc = _encode_userinfo_component(username)
    password_enc = _encode_userinfo_component(password)

    if password_enc:
        userinfo_enc = f"{username_enc}:{password_enc}"
    else:
        userinfo_enc = username_enc

    netloc = f"{userinfo_enc}@{hostinfo}" if userinfo_enc else hostinfo
    return urlunparse(parsed._replace(netloc=netloc))


__all__ = ["normalize_database_url"]