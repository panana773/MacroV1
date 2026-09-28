from __future__ import annotations

import threading

from collections.abc import Callable

from datetime import (
    datetime,
    time as dt_time,
    timedelta
)

from .server_time import ServerTime


TriggerCallback = Callable[
    [],
    None
]

StatusCallback = Callable[
    [str],
    None
]


class Scheduler:
    def __init__(
        self,
        server_time: ServerTime
    ) -> None:

        self.server_time = server_time

        self._lock = (
            threading.Lock()
        )

        self._stop_event: (
            threading.Event | None
        ) = None

        self._thread: (
            threading.Thread | None
        ) = None

        self._active = False

        self._target_datetime: (
            datetime | None
        ) = None

    @property
    def is_active(self) -> bool:

        with self._lock:
            return self._active

    @property
    def target_datetime(
        self
    ) -> datetime | None:

        with self._lock:
            return (
                self._target_datetime
            )

    def start(
        self,
        target_time: dt_time,
        on_trigger: TriggerCallback,
        on_status:
        StatusCallback | None = None,
    ) -> datetime:

        if not self.server_time.is_synced:

            raise RuntimeError(
                "먼저 서버 시간을 "
                "동기화해주세요."
            )

        self.cancel()

        now = self.server_time.now()

        target = datetime.combine(
            now.date(),
            target_time,
            tzinfo=now.tzinfo
        )

        # 이미 오늘 목표 시간이 지났으면
        # 다음 날 같은 시각으로 예약
        if target <= now:

            target += timedelta(
                days=1
            )

        stop_event = (
            threading.Event()
        )

        with self._lock:

            self._stop_event = (
                stop_event
            )

            self._active = True

            self._target_datetime = (
                target
            )

            self._thread = (
                threading.Thread(
                    target=self._run,
                    args=(
                        target,
                        stop_event,
                        on_trigger,
                        on_status
                    ),
                    daemon=True
                )
            )

            self._thread.start()

        return target

    def cancel(self) -> None:

        with self._lock:

            if (
                self._stop_event
                is not None
            ):

                self._stop_event.set()

            self._active = False

            self._target_datetime = None

    def _run(
        self,
        target: datetime,
        stop_event:
        threading.Event,
        on_trigger:
        TriggerCallback,
        on_status:
        StatusCallback | None,
    ) -> None:

        while not (
            stop_event.is_set()
        ):

            now = (
                self.server_time.now()
            )

            remaining = (
                target
                - now
            ).total_seconds()

            if remaining <= 0:

                with self._lock:

                    if (
                        stop_event
                        is not
                        self._stop_event
                        or not
                        self._active
                    ):

                        return

                    self._active = False

                    self._target_datetime = (
                        None
                    )

                if on_status:

                    on_status(
                        "예약 시간 도달"
                    )

                on_trigger()

                return

            if remaining > 2:

                wait_time = min(
                    0.25,
                    remaining - 1
                )

            elif remaining > 0.2:

                wait_time = 0.02

            else:

                wait_time = 0.001

            stop_event.wait(
                max(
                    wait_time,
                    0.0005
                )
            )