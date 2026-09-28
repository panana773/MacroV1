from __future__ import annotations

import statistics
import time

from dataclasses import dataclass

from datetime import (
    datetime,
    timedelta,
    timezone
)

from email.utils import parsedate_to_datetime

import requests


@dataclass(frozen=True)
class SyncResult:
    url: str
    offset_seconds: float
    median_rtt_ms: float
    samples: int


class ServerTime:
    def __init__(self) -> None:

        self._synced = False

        self._source_url = ""

        self._offset_seconds = 0.0

        self._anchor_server_utc: (
            datetime | None
        ) = None

        self._anchor_perf = 0.0

    @property
    def is_synced(self) -> bool:
        return self._synced

    @property
    def source_url(self) -> str:
        return self._source_url

    @property
    def offset_seconds(self) -> float:
        return self._offset_seconds

    def sync(
        self,
        url: str,
        samples: int = 5,
        timeout: float = 5.0
    ) -> SyncResult:

        url = self._normalize_url(url)

        offsets = []

        rtts_ms = []

        session = requests.Session()

        session.headers.update({
            "User-Agent": "MacroV1/1.0",
            "Cache-Control": "no-cache",
        })

        try:

            for _ in range(samples):

                start_wall = datetime.now(
                    timezone.utc
                )

                start_perf = (
                    time.perf_counter()
                )

                response = session.head(
                    url,
                    timeout=timeout,
                    allow_redirects=True,
                    headers={
                        "Cache-Control":
                        "no-cache"
                    },
                )

                if response.status_code in (
                    405,
                    501
                ):

                    response = session.get(
                        url,
                        timeout=timeout,
                        allow_redirects=True,
                        stream=True,
                        headers={
                            "Cache-Control":
                            "no-cache"
                        },
                    )

                end_wall = datetime.now(
                    timezone.utc
                )

                end_perf = (
                    time.perf_counter()
                )

                date_header = (
                    response.headers.get(
                        "Date"
                    )
                )

                if not date_header:

                    raise RuntimeError(
                        "서버 응답에서 "
                        "HTTP Date 헤더를 "
                        "찾을 수 없습니다."
                    )

                server_utc = (
                    parsedate_to_datetime(
                        date_header
                    )
                )

                if server_utc.tzinfo is None:

                    server_utc = (
                        server_utc.replace(
                            tzinfo=timezone.utc
                        )
                    )

                else:

                    server_utc = (
                        server_utc.astimezone(
                            timezone.utc
                        )
                    )

                midpoint = (
                    start_wall
                    + (end_wall - start_wall)
                    / 2
                )

                offset = (
                    server_utc
                    - midpoint
                ).total_seconds()

                offsets.append(offset)

                rtts_ms.append(
                    (
                        end_perf
                        - start_perf
                    )
                    * 1000
                )

                time.sleep(0.08)

        finally:

            session.close()

        if not offsets:

            raise RuntimeError(
                "서버 시간 측정에 실패했습니다."
            )

        median_offset = (
            statistics.median(
                offsets
            )
        )

        median_rtt = (
            statistics.median(
                rtts_ms
            )
        )

        self._offset_seconds = (
            median_offset
        )

        self._source_url = url

        self._anchor_server_utc = (
            datetime.now(timezone.utc)
            + timedelta(
                seconds=median_offset
            )
        )

        self._anchor_perf = (
            time.perf_counter()
        )

        self._synced = True

        return SyncResult(
            url=url,
            offset_seconds=median_offset,
            median_rtt_ms=median_rtt,
            samples=len(offsets),
        )

    def now(self) -> datetime:

        if (
            not self._synced
            or self._anchor_server_utc
            is None
        ):

            raise RuntimeError(
                "서버 시간이 아직 "
                "동기화되지 않았습니다."
            )

        elapsed = (
            time.perf_counter()
            - self._anchor_perf
        )

        server_utc = (
            self._anchor_server_utc
            + timedelta(
                seconds=elapsed
            )
        )

        return server_utc.astimezone()

    @staticmethod
    def _normalize_url(
        url: str
    ) -> str:

        url = url.strip()

        if not url:

            raise ValueError(
                "서버 URL을 입력해주세요."
            )

        if not url.startswith(
            (
                "http://",
                "https://"
            )
        ):

            url = (
                "https://"
                + url
            )

        return url