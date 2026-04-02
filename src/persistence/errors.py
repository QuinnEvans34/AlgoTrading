"""Persistence-layer exceptions."""

from __future__ import annotations


class PersistenceError(Exception):
    """Base persistence error."""


class PersistenceUnavailableError(PersistenceError):
    """Raised when the configured database cannot be reached or queried."""
