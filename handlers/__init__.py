"""Bot handlers."""
from aiogram import Router

from . import start, search, admin, ad_management, social, shazam


def get_routers() -> list[Router]:
    """Get all handler routers."""
    return [
        start.router,
        social.router,
        shazam.router, # Handle media files
        search.router,
        admin.router,
        ad_management.router,
    ]


__all__ = ["get_routers"]
