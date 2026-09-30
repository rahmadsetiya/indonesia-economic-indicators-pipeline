from __future__ import annotations

from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class HttpResponse:
    body: bytes
    status: int
    media_type: str
    final_url: str


def fetch(url: str, timeout_seconds: int = 30, user_agent: str = "iei-pipeline/0.1") -> HttpResponse:
    request = Request(url, headers={"User-Agent": user_agent, "Accept": "*/*"})
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            return HttpResponse(
                body=response.read(),
                status=response.status,
                media_type=response.headers.get_content_type(),
                final_url=response.geturl(),
            )
    except HTTPError as exc:
        raise RuntimeError(f"HTTP {exc.code} while retrieving {url}") from exc
    except URLError as exc:
        raise RuntimeError(f"failed to retrieve {url}: {exc.reason}") from exc
