"""
Porkbun CLI - Domain and DNS management tool
Author: Luke Steuber
"""

__version__ = "1.0.0"
__author__ = "Luke Steuber"

from .api import DNS_TYPES, PorkbunAPI

__all__ = ["PorkbunAPI", "DNS_TYPES", "__version__"]
