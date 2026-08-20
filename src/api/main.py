from core.middleware import register_exception_handlers
from fastapi.responses import ORJSONResponse
from fastapi import FastAPI
from core.logger import setup_logger
from core.middleware import RequestIDMiddleware
from api.routers import chat, system, document_router

setup_logger()

app = FastAPI(
    title="RAG SaaS Platform API",
    description="Enterprise AI-powered Retrieval-Augmented Generation",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    default_response_class=ORJSONResponse,
)

app.add_middleware(RequestIDMiddleware)

register_exception_handlers(app)

app.include_router(system.router)
app.include_router(chat.router)
app.include_router(document_router.router)
