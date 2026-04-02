"""Explicit error types for grounded asset research."""

from __future__ import annotations


class AssetResearchUnavailableError(RuntimeError):
    """Raised when asset research cannot run because configuration is missing."""


class AssetResearchProviderError(RuntimeError):
    """Raised when an upstream model provider request fails."""
