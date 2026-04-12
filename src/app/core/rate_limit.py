import asyncio
import time
from collections import deque
from typing import Deque, Dict, Optional, Tuple

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.config import rate_limit_route_policies
from app.core.logger import get_logger

logger = get_logger(__name__)


class RateLimitStore:
    def __init__(self):
        self.data: Dict[str, Deque[float]] = {}
        self.lock = asyncio.Lock()

    async def allow_request(
        self,
        key: str,
        max_requests: int,
        window_seconds: int,
    ) -> bool:
        now = time.monotonic()
        async with self.lock:
            history = self.data.setdefault(key, deque())
            while history and history[0] <= now - window_seconds:
                history.popleft()
            if len(history) >= max_requests:
                return False
            history.append(now)
            return True


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        default_max_requests: int = 60,
        default_window_seconds: int = 60,
        max_requests: Optional[int] = None,
        window_seconds: Optional[int] = None,
        exempt_paths: Optional[set[str]] = None,
    ):
        super().__init__(app)
        self.store = RateLimitStore()
        self.default_max_requests = max_requests if max_requests is not None else default_max_requests
        self.default_window_seconds = window_seconds if window_seconds is not None else default_window_seconds
        self.policies = rate_limit_route_policies()
        self.exempt_paths = exempt_paths or {
            "/docs",
            "/openapi.json",
            "/health",
            "/",
            "/ui",
            "/podcast-player",
            "/voice-library",
        }

    async def dispatch(self, request: Request, call_next):
        if request.method == "OPTIONS" or request.url.path in self.exempt_paths:
            return await call_next(request)

        rate_key = self._get_rate_key(request)
        route_key, max_requests, window_seconds = self._get_route_policy(request.url.path)
        bucket = f"{rate_key}:{route_key}"

        allowed = await self.store.allow_request(bucket, max_requests, window_seconds)
        if not allowed:
            logger.warning(
                "Rate limit exceeded for %s %s %s [%s/%ss]",
                rate_key,
                request.method,
                request.url.path,
                max_requests,
                window_seconds,
            )
            return Response(
                content=(
                    f"Too many requests for {request.url.path}. "
                    f"Limit is {max_requests} requests per {window_seconds} seconds."
                ),
                status_code=429,
                media_type="text/plain",
            )

        return await call_next(request)

    def _get_rate_key(self, request: Request) -> str:
        api_key = request.headers.get("x-api-key")
        if api_key:
            return f"api_key:{api_key}"
        xff = request.headers.get("x-forwarded-for")
        if xff:
            return f"ip:{xff.split(',')[0].strip()}"
        client = request.client
        return f"ip:{client.host if client else 'unknown'}"

    def _get_route_policy(self, path: str) -> Tuple[str, int, int]:
        normalized = path.lower()
        if normalized in self.policies:
            max_req, window = self.policies[normalized]
            return normalized, max_req, window

        # Prefix matching for endpoints like /transcribe, /upload
        for route_prefix, policy in self.policies.items():
            if normalized.startswith(route_prefix):
                max_req, window = policy
                return route_prefix, max_req, window

        return "/default", self.default_max_requests, self.default_window_seconds
