"""KTDB API 클라이언트 모듈."""

from __future__ import annotations

import abc
from typing import Any

import httpx


class KTDBAPIError(Exception):
    pass


class BaseAPIClient(abc.ABC):
    """KTDB API 커넥터 기본 클래스."""

    BASE_URL = "https://www.ktdb.go.kr/api"

    def __init__(self, api_key: str, timeout: float = 30.0) -> None:
        self.api_key = api_key
        self.timeout = timeout
        self._client: httpx.Client | None = None

    def __enter__(self) -> BaseAPIClient:
        self._client = httpx.Client(timeout=self.timeout)
        return self

    def __exit__(self, *args: Any) -> None:
        if self._client:
            self._client.close()

    def _get(self, endpoint: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        raise NotImplementedError

    def _post(self, endpoint: str, payload: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError


class ODMatrixClient(BaseAPIClient):
    """OD 매트릭스 데이터 수집 클라이언트."""

    def fetch_od_matrix(
        self,
        year: int,
        zone_system: str,
        trip_purpose: str | None = None,
    ) -> dict[str, Any]:
        raise NotImplementedError

    def fetch_zone_info(self, zone_system: str) -> dict[str, Any]:
        raise NotImplementedError


class SocioeconomicClient(BaseAPIClient):
    """사회경제지표 데이터 수집 클라이언트."""

    def fetch_population(self, year: int, region_code: str | None = None) -> dict[str, Any]:
        raise NotImplementedError

    def fetch_employment(self, year: int, region_code: str | None = None) -> dict[str, Any]:
        raise NotImplementedError

    def fetch_vehicle_registration(self, year: int) -> dict[str, Any]:
        raise NotImplementedError
