import logging
import time

from fastapi import Request, Response

logger = logging.getLogger(__name__)


async def logging_middleware(request: Request, call_next):
    start = time.time()
    logger.info(f"[middleware] 请求开始: {request.method} {request.url.path}")

    try:
        response: Response = await call_next(request)
        elapsed = time.time() - start
        logger.info(f"[middleware] 请求完成: {request.method} {request.url.path} - {response.status_code} ({elapsed:.2f}s)")
        return response
    except Exception as e:
        elapsed = time.time() - start
        logger.exception(f"[middleware] 请求异常: {request.method} {request.url.path} - {type(e).__name__}: {str(e)} ({elapsed:.2f}s)")
        raise
