from fastapi import FastAPI
from core.logger import setup_logger
from core.middleware import RequestIDMiddleware
from api.routers import chat, system

setup_logger()

app = FastAPI(
    title="RAG SaaS Platform API",
    description="Enterprise AI-powered Retrieval-Augmented Generation",
    version="0.1.0"
)

app.add_middleware(RequestIDMiddleware)

app.include_router(system.router)
app.include_router(chat.router)