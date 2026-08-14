from core.exceptions import (
    BaseAppError,
    NotFoundError,
    AIProviderError,
    RateLimitExceededError,
    ValidationError,
)
from fastapi.responses import JSONResponse
from fastapi import FastAPI
import time
import uuid
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from core.logger import logger

class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        # Attach request id to context or request state
        request.state.request_id = request_id

        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time

        logger.info(
            "request_completed",
            method=request.method,
            url=str(request.url),
            request_id=request_id,
            process_time_ms=round(process_time * 1000, 2),
            status_code=response.status_code
        )
        response.headers["X-Request-ID"] = request_id
        return response

def register_exception_handlers(app: FastAPI) -> None:

    @app.exception_handler(RateLimitExceededError)
    async def _rate_limit_handler(request: Request, exc: RateLimitExceededError) -> JSONResponse:
        logger.warning("rate_limit.exceeded", detail=str(exc))
        return JSONResponse(status_code=429, content={"detail": str(exc)})

    @app.exception_handler(AIProviderError)
    async def _provider_handler(request: Request, exc: AIProviderError) -> JSONResponse:
        logger.error("provider.error", detail=str(exc))
        return JSONResponse(status_code=503, content={"detail": str(exc)})

    @app.exception_handler(NotFoundError)
    async def _not_found_handler(request: Request, exc: NotFoundError) -> JSONResponse:
        logger.warning("resource.not_found", detail=str(exc))
        return JSONResponse(status_code=404, content={"detail": str(exc)})
        
    @app.exception_handler(ValidationError)
    async def _validation_handler(request: Request, exc: ValidationError) -> JSONResponse:
        logger.warning("validation.error", detail=str(exc))
        return JSONResponse(status_code=400, content={"detail": str(exc)})
        
    # Catch all other base app errors, which will be logged as rag_app.error
    @app.exception_handler(BaseAppError)
    async def _generic_handler(request: Request, exc: BaseAppError) -> JSONResponse:
        # Determine status code based on exception type if needed, or default to 500
        status_code = 500
        if exc.__class__.__name__ in ["AuthenticationError"]:
            status_code = 401
        elif exc.__class__.__name__ in ["AuthorizationError"]:
            status_code = 403
        elif exc.__class__.__name__ in ["InvalidRequestError"]:
            status_code = 400
            
        logger.error("rag_app.error", exc_type=exc.__class__.__name__, detail=str(exc))
        return JSONResponse(status_code=status_code, content={"detail": str(exc)})

