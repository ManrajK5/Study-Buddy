from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import analytics, calendar, chat, courses, events, health, upload
from app.core.config import settings
from app.core.logging import configure_logging, get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    logger.info("study_buddy_api_starting", environment=settings.app_env)
    yield
    logger.info("study_buddy_api_stopping")


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="AI academic planning assistant with PDF extraction, RAG, and LangGraph workflows.",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router, prefix=settings.api_v1_prefix)
    app.include_router(courses.router, prefix=settings.api_v1_prefix)
    app.include_router(upload.router, prefix=settings.api_v1_prefix)
    app.include_router(chat.router, prefix=settings.api_v1_prefix)
    app.include_router(analytics.router, prefix=settings.api_v1_prefix)
    app.include_router(calendar.router, prefix=settings.api_v1_prefix)
    app.include_router(events.router, prefix=settings.api_v1_prefix)
    return app


app = create_app()
