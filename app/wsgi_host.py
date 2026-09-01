"""Compatibility import. PythonAnywhere should load top-level wsgi.py."""

from wsgi import application

__all__ = ["application"]
