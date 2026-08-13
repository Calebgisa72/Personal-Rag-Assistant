import time
import uuid
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from src.core.logger import logger

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