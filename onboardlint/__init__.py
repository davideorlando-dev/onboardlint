"""OnboardLint: audit the first-time contributor experience."""

from .core import AuditReport, Finding, RepositoryReadError, audit_repository

__all__ = ["AuditReport", "Finding", "RepositoryReadError", "audit_repository"]
__version__ = "0.1.0"
