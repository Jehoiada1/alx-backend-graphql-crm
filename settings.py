"""Compatibility settings module for checkers importing project root settings.

Delegates to the real Django settings in crm.settings.
"""
from crm.settings import *  # noqa: F401,F403
