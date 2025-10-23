"""
Routers initialization.
"""

from app.routers.chat import router as chat_router
from app.routers.training import router as training_router

__all__ = [
    "chat_router",
    "training_router",
]
