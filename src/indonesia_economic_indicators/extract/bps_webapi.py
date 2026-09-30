from __future__ import annotations

from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class BpsApiResponse:
    body: bytes
    status: int
    media_type: str
    source_url: str
    original_filename: str


class BpsApiError(RuntimeError):
    pass


class BpsWebApiClient:
    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = "https://webapi.bps.go.id/",
        timeout_seconds: int = 30,
    ) -> None:
        if not api_key:
            raise ValueError("BPS API key is required")
        self._api_key = api_key
        self._base_url = base_url.rstrip("/") + "/"
        self._timeout_seconds = timeout_seconds

    def _get(self, relative_path: str, *, original_filename: str) -> BpsApiResponse:
        public_url = self._base_url + relative_path.strip("/")
        private_url = public_url + "/key/" + quote(self._api_key, safe="")
        request = Request(
            private_url,
            headers={"Accept": "application/json", "User-Agent": "iei-pipeline/0.1"},
        )
        try:
            with urlopen(request, timeout=self._timeout_seconds) as response:
                return BpsApiResponse(
                    body=response.read(),
                    status=response.status,
                    media_type=response.headers.get_content_type(),
                    source_url=public_url,
                    original_filename=original_filename,
                )
        except HTTPError as exc:
            return BpsApiResponse(
                body=exc.read(),
                status=exc.code,
                media_type=exc.headers.get_content_type(),
                source_url=public_url,
                original_filename=original_filename,
            )
        except URLError as exc:
            reason = type(exc.reason).__name__
            raise BpsApiError(f"BPS WebAPI network failure: {reason}") from None

    def fetch_period_page(self, variable_id: int, page: int) -> BpsApiResponse:
        if variable_id <= 0 or page <= 0:
            raise ValueError("BPS variable ID and page must be positive")
        path = f"v1/api/list/model/th/domain/0000/var/{variable_id}/page/{page}"
        return self._get(
            path,
            original_filename=f"bps_var_{variable_id}_periods_page_{page}.json",
        )

    def fetch_data(self, variable_id: int, period_ids: list[int]) -> BpsApiResponse:
        if variable_id <= 0:
            raise ValueError("BPS variable ID must be positive")
        unique_ids = sorted(set(period_ids))
        if len(unique_ids) != len(period_ids) or not 1 <= len(unique_ids) <= 3:
            raise ValueError("BPS data request requires one to three unique period IDs")
        if unique_ids == list(range(unique_ids[0], unique_ids[-1] + 1)):
            selector = f"{unique_ids[0]}:{unique_ids[-1]}"
        else:
            selector = ";".join(str(item) for item in unique_ids)
        path = f"v1/api/list/model/data/domain/0000/var/{variable_id}/th/{selector}"
        return self._get(
            path,
            original_filename=f"bps_var_{variable_id}_data_th_{selector.replace(':', '-')}.json",
        )
