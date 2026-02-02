# discovery/app/middleware/__init__.py
"""Middleware components for Discovery service."""
from app.middleware.error_handler import add_exception_handlers

__all__ = ["add_exception_handlers"]
