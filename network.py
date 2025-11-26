"""Wrapper module: network.py

This project previously had an alternate network implementation in
`network.py`. To avoid confusion with the primary `network_manager.py`,
the legacy implementation was moved to `network_legacy.py` and this module
imports from there to preserve backwards compatibility.
"""

from .network_legacy import *  # noqa: F401,F403

__all__ = ["NetworkManager"]