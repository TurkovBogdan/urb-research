"""The refusal every update step raises; the message is what the operator reads."""

from __future__ import annotations


class UpdateRefused(RuntimeError):
    """A step said no; the message is what the operator reads."""


__all__ = ["UpdateRefused"]
