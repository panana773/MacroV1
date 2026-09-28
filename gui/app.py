from __future__ import annotations

import queue
import threading
import tkinter as tk

from datetime import datetime

from tkinter import (
    messagebox,
    ttk
)

from pynput import mouse

from config.config_manager import (
    ConfigManager
)

from core.click_engine import (
    ClickEngine
)

from core.hotkeys import (
    HotkeyManager
)

from core.queue_manager import (
    QueueManager
)

from core.scheduler import (
    Scheduler
)

from core.server_time import (
    ServerTime,
    SyncResult
)


class MacroApp:
    def __init__(self) -> None:

        self.root = tk.Tk()

        self.root.title(
            "Macro V1"
        )

        self.root.geometry(
            "920x720"
        )

        self.root.minsize(
            880,
            680
        )

        self.ui_tasks = (
            queue.Queue()
        )

        self.mouse_controller = (
            mouse.Controller()
        )

        # -----------------------
        # 설정
        # -----------------------

        self.config_manager = (
            ConfigManager()
        )

        self.config = (
            self.config_manager.load()
        )

        # -----------------------
        # 기능 모듈
        # -----------------------

        self.queue_manager = (
            QueueManager()
        )

        self.queue_manager.set_positions(
            self.config.get(
                "click_queue",
                []
            )
        )

        self.server_time = (
            ServerTime()
        )

        self.click_engine = (
            ClickEngine()
        )

        self.scheduler = (
            Scheduler(
                self.server_time
            )
        )

        self.register_key = str(
            self.config.get(
                "register_key",
                "h"
            )
        ).lower()

        self.execute_key = str(
            self.config.get(
                "execute_key",
                "s"
            )
        ).lower()

        # -----------------------
        # 단축키
        # -----------------------

        self.hotkeys = (
            HotkeyManager(

                on_register=lambda:
                self._post_ui(
                    lambda:
                    self.register_position(
                        from_hotkey=True
                    )
                ),

                on_execute=lambda:
                self._post_ui(
                    lambda:
                    self.execute_queue(
                        source="단축키"
                    )
                ),

                on_stop=lambda:
                self._post_ui(
                    self.emergency_stop
                ),

                register_key=
                self.register_key,

                execute_key=
                self.execute_key,
            )
        )

        # -----------------------
        # GUI
        # -----------------------

        self._build_ui()

        self._load_config_into_ui()

        self._refresh_queue()

        self.root.protocol(
            "WM_DELETE_WINDOW",
            self._on_close
        )

    # =====================================================
    # 실행
    # =====================================================

    def run(self) -> None:

        self.hotkeys.start()

        self._process_ui_tasks()

        self._update_mouse_position()

        self._update_server_clock()

        self.root.mainloop()

    # =====================================================
    # Thread → GUI 전달
    # =====================================================

    def _post_ui(
        self,
        callback
    ) -> None:

        self.ui_tasks.put(
            callback
        )

    def _process_ui_tasks(
        self
    ) -> None:

        try:

            while True:

                callback = (
                    self.ui_tasks
                    .get_nowait()
                )

                callback()

        except queue.Empty:
            pass

        self.root.after(
            10,
            self._process_ui_tasks
        )

    # =====================================================
    # 전체 UI
    # =====================================================

    def _build_ui(self) -> None:

        self.root.columnconfigure(
            0,
            weight=1
        )

        self.root.rowconfigure(
            2,
            weight=1
        )

        self._build_server_section()

        self._build_reservation_section()

        self._build_middle_section()

        self._build_control_section()

        self._build_status_section()

    # =====================================================
    # 서버 UI
    # =====================================================

    def _build_server_section(
        self
    ) -> None:

        frame = ttk.LabelFrame(
            self.root,
            text="서버 시간"
        )

        frame.pack(
            fill="x",
            padx=18,
            pady=(14, 6)
        )

        frame.columnconfigure(
            1,
            weight=1
        )

        ttk.Label(
            frame,
            text="서버 URL"
        ).grid(
            row=0,
            column=0,
            padx=10,
            pady=10,
            sticky="w"
        )

        self.url_entry = (
            ttk.Entry(frame)
        )

        self.url_entry.grid(
            row=0,
            column=1,
            padx=8,
            pady=10,
            sticky="ew"
        )

        self.sync_button = (
            ttk.Button(
                frame,
                text="동기화",
                command=
                self.sync_server
            )
        )

        self.sync_button.grid(
            row=0,
            column=2,
            padx=10,
            pady=10
        )

        ttk.Label(
            frame,
            text="현재 서버 시간"
        ).grid(
            row=1,
            column=0,
            padx=10,
            pady=(2, 4),
            sticky="w"
        )

        self.server_time_label = (
            ttk.Label(
                frame,
                text="--:--:--.---",
                font=(
                    "Consolas",
                    22,
                    "bold"
                )
            )
        )

        self.server_time_label.grid(
            row=1,
            column=1,
            padx=8,
            pady=(2, 4),
            sticky="w"
        )

        self.offset_label = (
            ttk.Label(
                frame,
                text="PC와 차이 : ---"
            )
        )

        self.offset_label.grid(
            row=2,
            column=1,
            padx=8,
            pady=(0, 2),
            sticky="w"
        )

        self.rtt_label = (
            ttk.Label(
                frame,
                text="측정 RTT : ---"
            )
        )

        self.rtt_label.grid(
            row=3,
            column=1,
            padx=8,
            pady=(0, 4),
            sticky="w"
        )

        ttk.Label(
            frame,
            text=(
                "※ 현재 V1은 HTTP Date "
                "헤더 기준이며 밀리초 단위 "
                "정확도는 보장되지 않습니다."
            )
        ).grid(
            row=4,
            column=0,
            columnspan=3,
            padx=10,
            pady=(0, 8),
            sticky="w"
        )

    # =====================================================
    # 예약 UI
    # =====================================================

    def _build_reservation_section(
        self
    ) -> None:

        frame = ttk.LabelFrame(
            self.root,
            text="예약 실행"
        )

        frame.pack(
            fill="x",
            padx=18,
            pady=6
        )

        ttk.Label(
            frame,
            text="목표 시간"
        ).pack(
            side="left",
            padx=(10, 6),
            pady=10
        )

        self.target_entry = (
            ttk.Entry(
                frame,
                width=18
            )
        )

        self.target_entry.pack(
            side="left",
            padx=6,
            pady=10
        )

        ttk.Label(
            frame,
            text="예: 10:00:00.000"
        ).pack(
            side="left",
            padx=(0, 12)
        )

        self.reserve_button = (
            ttk.Button(
                frame,
                text="예약 시작",
                command=
                self.toggle_reservation
            )
        )

        self.reserve_button.pack(
            side="left",
            padx=6
        )

        self.reservation_label = (
            ttk.Label(
                frame,
                text="예약 없음"
            )
        )

        self.reservation_label.pack(
            side="left",
            padx=14
        )

    # =====================================================
    # 마우스 / Queue UI
    # =====================================================

    def _build_middle_section(
        self
    ) -> None:

        middle = ttk.Frame(
            self.root
        )

        middle.pack(
            fill="both",
            expand=True,
            padx=18,
            pady=6
        )

        # -----------------------
        # 왼쪽
        # -----------------------

        mouse_frame = (
            ttk.LabelFrame(
                middle,
                text="마우스 / 단축키"
            )
        )

        mouse_frame.pack(
            side="left",
            fill="both",
            expand=True,
            padx=(0, 5)
        )

        self.mouse_position_label = (
            ttk.Label(
                mouse_frame,
                text=(
                    "현재 위치\n\n"
                    "X : ---\n"
                    "Y : ---"
                ),
                font=(
                    "Consolas",
                    15
                ),
                justify="left"
            )
        )

        self.mouse_position_label.pack(
            pady=(30, 20)
        )

        ttk.Separator(
            mouse_frame,
            orient="horizontal"
        ).pack(
            fill="x",
            padx=20,
            pady=8
        )

        ttk.Label(
            mouse_frame,
            text=(
                f"{self.register_key.upper()}"
                "  : 현재 좌표 Queue 등록"
            )
        ).pack(
            anchor="w",
            padx=28,
            pady=5
        )

        ttk.Label(
            mouse_frame,
            text=(
                f"{self.execute_key.upper()}"
                "  : Queue 즉시 실행"
            )
        ).pack(
            anchor="w",
            padx=28,
            pady=5
        )

        ttk.Label(
            mouse_frame,
            text=(
                "ESC : 긴급 정지 + 예약 취소"
            )
        ).pack(
            anchor="w",
            padx=28,
            pady=5
        )

        # -----------------------
        # 오른쪽 Queue
        # -----------------------

        queue_frame = (
            ttk.LabelFrame(
                middle,
                text="클릭 Queue"
            )
        )

        queue_frame.pack(
            side="right",
            fill="both",
            expand=True,
            padx=(5, 0)
        )

        list_container = (
            ttk.Frame(
                queue_frame
            )
        )

        list_container.pack(
            fill="both",
            expand=True,
            padx=10,
            pady=10
        )

        self.queue_list = (
            tk.Listbox(
                list_container,
                font=(
                    "Consolas",
                    11
                ),
                exportselection=False
            )
        )

        self.queue_list.pack(
            side="left",
            fill="both",
            expand=True
        )

        scrollbar = (
            ttk.Scrollbar(
                list_container,
                orient="vertical",
                command=
                self.queue_list.yview
            )
        )

        scrollbar.pack(
            side="right",
            fill="y"
        )

        self.queue_list.config(
            yscrollcommand=
            scrollbar.set
        )

        queue_buttons = (
            ttk.Frame(
                queue_frame
            )
        )

        queue_buttons.pack(
            pady=(0, 7)
        )

        ttk.Button(
            queue_buttons,
            text="↑",
            width=5,
            command=self.move_up
        ).pack(
            side="left",
            padx=3
        )

        ttk.Button(
            queue_buttons,
            text="↓",
            width=5,
            command=self.move_down
        ).pack(
            side="left",
            padx=3
        )

        ttk.Button(
            queue_buttons,
            text="삭제",
            command=
            self.delete_position
        ).pack(
            side="left",
            padx=3
        )

        ttk.Button(
            queue_buttons,
            text="Queue 초기화",
            command=
            self.clear_queue
        ).pack(
            side="left",
            padx=3
        )

    # =====================================================
    # 실행 설정 UI
    # =====================================================

    def _build_control_section(
        self
    ) -> None:

        frame = ttk.LabelFrame(
            self.root,
            text="실행 설정"
        )

        frame.pack(
            fill="x",
            padx=18,
            pady=6
        )

        ttk.Label(
            frame,
            text="클릭 간격"
        ).pack(
            side="left",
            padx=(10, 6),
            pady=10
        )

        self.interval_entry = (
            ttk.Entry(
                frame,
                width=8
            )
        )

        self.interval_entry.pack(
            side="left",
            padx=4
        )

        ttk.Label(
            frame,
            text="ms"
        ).pack(
            side="left",
            padx=(0, 16)
        )

        ttk.Button(
            frame,
            text="▶ Queue 실행",
            command=lambda:
            self.execute_queue(
                source="버튼"
            )
        ).pack(
            side="left",
            padx=5
        )

        ttk.Button(
            frame,
            text="■ 긴급 정지",
            command=
            self.emergency_stop
        ).pack(
            side="left",
            padx=5
        )

        ttk.Button(
            frame,
            text="설정 저장",
            command=
            self.save_config
        ).pack(
            side="right",
            padx=10
        )

    # =====================================================
    # 상태 UI
    # =====================================================

    def _build_status_section(
        self
    ) -> None:

        frame = ttk.Frame(
            self.root
        )

        frame.pack(
            fill="x",
            padx=20,
            pady=(6, 14)
        )

        self.status_label = (
            ttk.Label(
                frame,
                text="상태 : 대기 중"
            )
        )

        self.status_label.pack(
            side="left"
        )

        self.progress_label = (
            ttk.Label(
                frame,
                text=(
                    "Queue : 0개"
                    "    진행 : 0 / 0"
                )
            )
        )

        self.progress_label.pack(
            side="right"
        )

    # =====================================================
    # 설정 불러오기
    # =====================================================

    def _load_config_into_ui(
        self
    ) -> None:

        self.url_entry.insert(
            0,
            str(
                self.config.get(
                    "server_url",
                    ""
                )
            )
        )

        self.target_entry.insert(
            0,
            str(
                self.config.get(
                    "target_time",
                    "10:00:00.000"
                )
            )
        )

        self.interval_entry.insert(
            0,
            str(
                self.config.get(
                    "click_interval_ms",
                    30
                )
            )
        )

    # =====================================================
    # 설정 저장
    # =====================================================

    def save_config(
        self,
        silent: bool = False
    ) -> bool:

        try:

            interval = (
                self._read_interval_ms()
            )

            data = {

                "server_url":
                self.url_entry.get().strip(),

                "target_time":
                self.target_entry.get().strip(),

                "click_interval_ms":
                interval,

                "register_key":
                self.register_key,

                "execute_key":
                self.execute_key,

                "click_queue":
                self.queue_manager.items(),
            }

            self.config_manager.save(
                data
            )

            if not silent:

                self._set_status(
                    "설정 저장 완료"
                )

            return True

        except Exception as exc:

            if not silent:

                messagebox.showerror(
                    "설정 저장 실패",
                    str(exc)
                )

            return False

    # =====================================================
    # 서버 동기화
    # =====================================================

    def sync_server(self) -> None:

        url = (
            self.url_entry
            .get()
            .strip()
        )

        if not url:

            messagebox.showwarning(
                "URL 없음",
                "서버 URL을 입력해주세요."
            )

            return

        self.sync_button.config(
            state="disabled"
        )

        self._set_status(
            "서버 시간 동기화 중..."
        )

        def worker() -> None:

            try:

                result = (
                    self.server_time.sync(
                        url
                    )
                )

                self._post_ui(
                    lambda r=result:
                    self._on_sync_success(
                        r
                    )
                )

            except Exception as exc:

                self._post_ui(
                    lambda e=str(exc):
                    self._on_sync_error(
                        e
                    )
                )

        threading.Thread(
            target=worker,
            daemon=True
        ).start()

    def _on_sync_success(
        self,
        result: SyncResult
    ) -> None:

        self.sync_button.config(
            state="normal"
        )

        self.url_entry.delete(
            0,
            tk.END
        )

        self.url_entry.insert(
            0,
            result.url
        )

        self.offset_label.config(
            text=(
                "PC와 차이 : "
                f"{result.offset_seconds:+.3f} sec"
            )
        )

        self.rtt_label.config(
            text=(
                "측정 RTT : "
                f"{result.median_rtt_ms:.1f} ms "
                f"({result.samples}회 중앙값)"
            )
        )

        self._set_status(
            "서버 시간 동기화 완료"
        )

    def _on_sync_error(
        self,
        error: str
    ) -> None:

        self.sync_button.config(
            state="normal"
        )

        self._set_status(
            "서버 시간 동기화 실패"
        )

        messagebox.showerror(
            "동기화 실패",
            error
        )

    def _update_server_clock(
        self
    ) -> None:

        if (
            self.server_time.is_synced
        ):

            try:

                now = (
                    self.server_time.now()
                )

                self.server_time_label.config(
                    text=(
                        now.strftime(
                            "%H:%M:%S.%f"
                        )[:-3]
                    )
                )

            except RuntimeError:
                pass

        self.root.after(
            20,
            self._update_server_clock
        )

    # =====================================================
    # 마우스
    # =====================================================

    def _update_mouse_position(
        self
    ) -> None:

        try:

            x, y = (
                self.mouse_controller
                .position
            )

            self.mouse_position_label.config(
                text=(
                    "현재 위치\n\n"
                    f"X : {x}\n"
                    f"Y : {y}"
                )
            )

        except Exception:
            pass

        self.root.after(
            50,
            self._update_mouse_position
        )

    # =====================================================
    # 좌표 등록
    # =====================================================

    def register_position(
        self,
        from_hotkey: bool = False
    ) -> None:

        if (
            from_hotkey
            and self._text_input_has_focus()
        ):
            return

        if (
            self.click_engine.is_running
        ):

            self._set_status(
                "실행 중에는 좌표를 "
                "등록할 수 없습니다."
            )

            return

        x, y = (
            self.mouse_controller.position
        )

        self.queue_manager.add(
            x,
            y
        )

        self._refresh_queue()

        self._set_status(
            f"좌표 등록 ({x}, {y})"
        )

    # =====================================================
    # Queue 관리
    # =====================================================

    def move_up(self) -> None:

        if self._queue_locked():
            return

        index = (
            self._selected_queue_index()
        )

        if index is None:
            return

        new_index = (
            self.queue_manager
            .move_up(index)
        )

        self._refresh_queue(
            select_index=new_index
        )

    def move_down(self) -> None:

        if self._queue_locked():
            return

        index = (
            self._selected_queue_index()
        )

        if index is None:
            return

        new_index = (
            self.queue_manager
            .move_down(index)
        )

        self._refresh_queue(
            select_index=new_index
        )

    def delete_position(
        self
    ) -> None:

        if self._queue_locked():
            return

        index = (
            self._selected_queue_index()
        )

        if index is None:
            return

        self.queue_manager.delete(
            index
        )

        self._refresh_queue()

        self._set_status(
            "좌표 삭제"
        )

    def clear_queue(
        self
    ) -> None:

        if self._queue_locked():
            return

        self.queue_manager.clear()

        self._refresh_queue()

        self._set_status(
            "Queue 초기화"
        )

    def _queue_locked(
        self
    ) -> bool:

        if (
            self.click_engine.is_running
        ):

            self._set_status(
                "실행 중에는 Queue를 "
                "수정할 수 없습니다."
            )

            return True

        return False

    def _selected_queue_index(
        self
    ) -> int | None:

        selected = (
            self.queue_list
            .curselection()
        )

        if not selected:

            self._set_status(
                "Queue에서 항목을 "
                "먼저 선택해주세요."
            )

            return None

        return int(
            selected[0]
        )

    def _refresh_queue(
        self,
        select_index:
        int | None = None
    ) -> None:

        self.queue_list.delete(
            0,
            tk.END
        )

        for (
            index,
            (x, y)
        ) in enumerate(
            self.queue_manager.items(),
            start=1
        ):

            self.queue_list.insert(
                tk.END,
                (
                    f"{index:>2}.   "
                    f"X: {x:<5} "
                    f"Y: {y}"
                )
            )

        total = len(
            self.queue_manager
        )

        self.progress_label.config(
            text=(
                f"Queue : {total}개"
                f"    진행 : 0 / {total}"
            )
        )

        if (
            select_index is not None
            and
            0 <= select_index < total
        ):

            self.queue_list.selection_set(
                select_index
            )

            self.queue_list.activate(
                select_index
            )

            self.queue_list.see(
                select_index
            )

    # =====================================================
    # Queue 실행
    # =====================================================

    def execute_queue(
        self,
        source: str = "수동"
    ) -> None:

        if (
            source == "단축키"
            and
            self._text_input_has_focus()
        ):

            return

        if (
            self.click_engine.is_running
        ):

            self._set_status(
                "이미 Queue가 "
                "실행 중입니다."
            )

            return

        positions = (
            self.queue_manager
            .snapshot()
        )

        if not positions:

            self._set_status(
                "Queue가 비어 있습니다."
            )

            return

        try:

            interval_ms = (
                self._read_interval_ms()
            )

        except ValueError as exc:

            messagebox.showerror(
                "클릭 간격 오류",
                str(exc)
            )

            return

        total = len(
            positions
        )

        self.progress_label.config(
            text=(
                "Queue : "
                f"{len(self.queue_manager)}개"
                f"    진행 : 0 / {total}"
            )
        )

        started = (
            self.click_engine.start(

                positions=positions,

                interval_ms=
                interval_ms,

                on_status=lambda text:
                self._post_ui(
                    lambda t=text:
                    self._set_status(t)
                ),

                on_progress=
                lambda current, count:
                self._post_ui(
                    lambda c=current,
                    t=count:
                    self._set_progress(
                        c,
                        t
                    )
                ),

                on_finished=
                lambda completed, error:
                self._post_ui(
                    lambda c=completed,
                    e=error:
                    self._on_click_finished(
                        c,
                        e
                    )
                ),
            )
        )

        if started:

            self._set_status(
                f"Queue 실행 시작 "
                f"({source})"
            )

        else:

            self._set_status(
                "Queue를 시작하지 "
                "못했습니다."
            )

    # =====================================================
    # 긴급 정지
    # =====================================================

    def emergency_stop(
        self
    ) -> None:

        was_running = (
            self.click_engine.is_running
        )

        was_reserved = (
            self.scheduler.is_active
        )

        self.click_engine.stop()

        self.scheduler.cancel()

        self.reserve_button.config(
            text="예약 시작"
        )

        self.reservation_label.config(
            text="예약 없음"
        )

        if (
            was_running
            or was_reserved
        ):

            self._set_status(
                "긴급 정지 요청"
            )

        else:

            self._set_status(
                "현재 실행 중인 "
                "작업이 없습니다."
            )

    def _set_progress(
        self,
        current: int,
        total: int
    ) -> None:

        self.progress_label.config(
            text=(
                "Queue : "
                f"{len(self.queue_manager)}개"
                f"    진행 : "
                f"{current} / {total}"
            )
        )

    def _on_click_finished(
        self,
        completed: bool,
        error: str | None
    ) -> None:

        if error:
            return

        if completed:

            total = len(
                self.queue_manager
            )

            self.progress_label.config(
                text=(
                    f"Queue : {total}개"
                    "    진행 : 완료"
                )
            )

    # =====================================================
    # 예약 실행
    # =====================================================

    def toggle_reservation(
        self
    ) -> None:

        if (
            self.scheduler.is_active
        ):

            self.scheduler.cancel()

            self.reserve_button.config(
                text="예약 시작"
            )

            self.reservation_label.config(
                text="예약 없음"
            )

            self._set_status(
                "예약 취소"
            )

            return

        if not (
            self.server_time.is_synced
        ):

            messagebox.showwarning(
                "시간 동기화 필요",
                "먼저 서버 시간을 "
                "동기화해주세요."
            )

            return

        if (
            len(self.queue_manager)
            == 0
        ):

            messagebox.showwarning(
                "Queue 없음",
                "먼저 클릭 좌표를 "
                "등록해주세요."
            )

            return

        try:

            target_time = (
                self._parse_target_time()
            )

        except ValueError as exc:

            messagebox.showerror(
                "시간 형식 오류",
                str(exc)
            )

            return

        try:

            target_datetime = (
                self.scheduler.start(

                    target_time=
                    target_time,

                    on_trigger=lambda:
                    self._post_ui(
                        self._scheduled_trigger
                    ),

                    on_status=
                    lambda text:
                    self._post_ui(
                        lambda t=text:
                        self._set_status(t)
                    )
                )
            )

        except Exception as exc:

            messagebox.showerror(
                "예약 실패",
                str(exc)
            )

            return

        self.reserve_button.config(
            text="예약 취소"
        )

        self.reservation_label.config(
            text=(
                target_datetime.strftime(
                    "%Y-%m-%d "
                    "%H:%M:%S.%f"
                )[:-3]
            )
        )

        self._set_status(
            "예약 대기 중"
        )

    def _scheduled_trigger(
        self
    ) -> None:

        self.reserve_button.config(
            text="예약 시작"
        )

        self.reservation_label.config(
            text="예약 없음"
        )

        self._set_status(
            "예약 시간 도달"
        )

        self.execute_queue(
            source="예약"
        )

    # =====================================================
    # 입력값
    # =====================================================

    def _parse_target_time(
        self
    ):

        value = (
            self.target_entry
            .get()
            .strip()
        )

        for fmt in (
            "%H:%M:%S.%f",
            "%H:%M:%S"
        ):

            try:

                return (
                    datetime.strptime(
                        value,
                        fmt
                    ).time()
                )

            except ValueError:
                continue

        raise ValueError(
            "목표 시간을 "
            "HH:MM:SS.mmm 형식으로 "
            "입력해주세요."
        )

    def _read_interval_ms(
        self
    ) -> int:

        value = (
            self.interval_entry
            .get()
            .strip()
        )

        try:

            interval = int(
                value
            )

        except ValueError as exc:

            raise ValueError(
                "클릭 간격은 정수(ms)로 "
                "입력해주세요."
            ) from exc

        if interval < 0:

            raise ValueError(
                "클릭 간격은 "
                "0 이상이어야 합니다."
            )

        return interval

    def _set_status(
        self,
        text: str
    ) -> None:

        self.status_label.config(
            text=f"상태 : {text}"
        )

    def _text_input_has_focus(
        self
    ) -> bool:

        try:

            focused = (
                self.root.focus_get()
            )

        except tk.TclError:

            return False

        return isinstance(
            focused,
            (
                tk.Entry,
                ttk.Entry,
                ttk.Spinbox
            )
        )

    # =====================================================
    # 종료
    # =====================================================

    def _on_close(
        self
    ) -> None:

        self.scheduler.cancel()

        self.click_engine.stop()

        self.hotkeys.stop()

        self.save_config(
            silent=True
        )

        self.root.destroy()