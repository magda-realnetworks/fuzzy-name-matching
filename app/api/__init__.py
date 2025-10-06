"""
Expose FastAPI routers and make the package importable.
"""

from .routes import router

__all__ = ["router"]
