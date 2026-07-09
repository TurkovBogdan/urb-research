"""Hashing utilities: deterministic fingerprints and content hashes."""

from __future__ import annotations

import hashlib
import secrets

# Hash length in hex chars. 22 chars = 88 bits of entropy (2^88 ≈ 3.1e26 values).
# Birthday-bound probability of at least one collision P ≈ n² / 2^89: ~1.6e-16 at
# 1e6 items, ~1.6e-12 at 1e8; the 50% point is around 6.6e13 (66 trillion) items.
# Comfortable margin for change-detection at our scale. Alphabet is strictly
# [0-9a-f] (hexdigest): URL-safe, no '_'/'-'/uppercase.
_HASH_LEN = 22


def _hex(data: bytes) -> str:
    """SHA-256, first 22 hex chars (88 bits, see _HASH_LEN)."""
    return hashlib.sha256(data).hexdigest()[:_HASH_LEN]


def dict_hash(params: dict[str, str]) -> str:
    """22-char hex fingerprint of a set of key-value pairs.

    Keys are sorted alphabetically before hashing, so insertion order does not
    matter.
    """
    canonical = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
    return _hex(canonical.encode())


def random_hash() -> str:
    """22-char random hex token (88 bits of entropy), same length/alphabet as the
    deterministic hashes above.

    Use for surrogate identifiers that have no natural dedup value — every call yields
    a fresh value (cryptographically-strong RNG). Stored bare as an entity code; a consumer
    may add a type prefix as presentation at its own boundary (see ``research.codes``).
    """
    return secrets.token_hex(_HASH_LEN // 2)


def text_hash(text: str | None) -> str:
    """22-char hex content hash (88 bits, see _HASH_LEN).

    Used for change-detection: producer and consumer compare the hash value to
    tell whether the content changed since the last processing. `None` and the
    empty string yield the same hash ("no content"). Text canonicalization
    happens UPSTREAM in the pipeline (content_processors.utils html_to_text / normalize_text);
    this function hashes the received string verbatim.
    """
    return _hex((text or "").encode("utf-8"))


__all__ = ["dict_hash", "text_hash", "random_hash"]
