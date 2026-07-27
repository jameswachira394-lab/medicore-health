import httpx
from fastapi import APIRouter, HTTPException, Request, Response, status

from app.core.config import ROUTE_MAP

router = APIRouter()

# Headers that must not be forwarded verbatim between hops (hop-by-hop /
# would corrupt content-length or encoding once httpx re-issues the request).
_STRIP_REQUEST_HEADERS = {"host", "content-length"}
_STRIP_RESPONSE_HEADERS = {"content-length", "transfer-encoding", "connection"}


@router.api_route(
    "/{prefix}/{rest_of_path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
)
async def proxy(prefix: str, rest_of_path: str, request: Request):
    """
    Reverse-proxies /{prefix}/... to the microservice that owns `prefix`,
    forwarding method, query string, body, and headers (including the
    Authorization bearer token) unchanged. Each downstream service still
    independently validates the JWT and enforces its own RBAC — the
    gateway is a routing layer, not a trust boundary substitute.
    """
    base_url = ROUTE_MAP.get(prefix)
    if not base_url:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Unknown service prefix '{prefix}'")

    target_url = f"{base_url}/{prefix}/{rest_of_path}".rstrip("/")
    headers = {k: v for k, v in request.headers.items() if k.lower() not in _STRIP_REQUEST_HEADERS}
    body = await request.body()

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            upstream = await client.request(
                request.method,
                target_url,
                params=request.query_params,
                headers=headers,
                content=body,
            )
    except httpx.ConnectError:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"'{prefix}' service is unreachable")
    except httpx.TimeoutException:
        raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail=f"'{prefix}' service timed out")

    response_headers = {k: v for k, v in upstream.headers.items() if k.lower() not in _STRIP_RESPONSE_HEADERS}
    return Response(content=upstream.content, status_code=upstream.status_code, headers=response_headers)
