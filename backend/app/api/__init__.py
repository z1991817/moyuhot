from app.api.chat import router as chat_router
from app.api.health import router as health_router
from app.api.home import router as home_router
from app.api.market import router as market_router
from app.api.sources import router as sources_router
from app.api.trends import router as trends_router

__all__ = [
    "chat_router",
    "home_router",
    "trends_router",
    "sources_router",
    "market_router",
    "health_router",
]
