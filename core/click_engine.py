from __future__ import annotations

import threading
import time
from collections.abc import Callable

import pyautogui


StatusCallback = Callable[[str], None]
ProgressCallback = Callable[[int, int], None]
FinishedCallback = Callable[[bool, str | None], None]


class ClickEngine:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

        # 클릭 간격은 우리가 직접 제어
        pyautogui.PAUSE = 0

        # 화면 좌측 상단으로 마우스를 옮기면
        # PyAutoGUI 자체 fail-safe도 작동
        pyautogui.FAILSAFE = True

    @property
    def is_running(self) -> bool:
        with self._lock:
            return (
                self._thread is not None
                and self._thread.is_alive()
            )

    def start(
        self,
        positions: list[tuple[int, int]],
        interval_ms: int,
        on_status: StatusCallback | None = None,
        on_progress: ProgressCallback | None = None,
        on_finished: FinishedCallback | None = None,
    ) -> bool:

        if not positions:
            return False

        if interval_ms < 0:
            raise ValueError(
                "클릭 간격은 0 이상이어야 합니다."
            )

        with self._lock:

            if (
                self._thread is not None
                and self._thread.is_alive()
            ):
                return False

            self._stop_event = threading.Event()

            queue_snapshot = positions.copy()

            self._thread = threading.Thread(
                target=self._run,
                args=(
                    queue_snapshot,
                    interval_ms,
                    self._stop_event,
                    on_status,
                    on_progress,
                    on_finished,
                ),
                daemon=True,
            )

            self._thread.start()

            return True

    def stop(self) -> None:
        self._stop_event.set()

    def _run(
        self,
        positions: list[tuple[int, int]],
        interval_ms: int,
        stop_event: threading.Event,
        on_status: StatusCallback | None,
        on_progress: ProgressCallback | None,
        on_finished: FinishedCallback | None,
    ) -> None:

        total = len(positions)

        error_message: str | None = None

        completed = False

        if on_status:
            on_status("Queue 실행 중")

        try:

            for index, (x, y) in enumerate(
                positions,
                start=1
            ):

                if stop_event.is_set():
                    break

                pyautogui.click(
                    x=x,
                    y=y
                )

                if on_progress:
                    on_progress(
                        index,
                        total
                    )

                if index == total:
                    completed = True
                    break

                self._interruptible_wait(
                    interval_ms / 1000.0,
                    stop_event
                )

                if stop_event.is_set():
                    break

        except pyautogui.FailSafeException:

            error_message = (
                "PyAutoGUI fail-safe가 작동했습니다."
            )

        except Exception as exc:

            error_message = str(exc)

        if (
            stop_event.is_set()
            and error_message is None
        ):

            if on_status:
                on_status("긴급 정지됨")

        elif error_message is not None:

            if on_status:
                on_status(
                    f"클릭 오류: {error_message}"
                )

        elif completed:

            if on_status:
                on_status(
                    "Queue 실행 완료"
                )

        if on_finished:

            on_finished(
                completed
                and not stop_event.is_set(),
                error_message
            )

    @staticmethod
    def _interruptible_wait(
        seconds: float,
        stop_event: threading.Event
    ) -> None:

        if seconds <= 0:
            return

        end_time = (
            time.perf_counter()
            + seconds
        )

        while not stop_event.is_set():

            remaining = (
                end_time
                - time.perf_counter()
            )

            if remaining <= 0:
                return

            stop_event.wait(
                min(
                    remaining,
                    0.005
                )
            )