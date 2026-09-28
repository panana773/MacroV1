from __future__ import annotations

from collections.abc import Callable

from pynput import keyboard


class HotkeyManager:
    def __init__(
        self,
        on_register: Callable[
            [],
            None
        ],
        on_execute: Callable[
            [],
            None
        ],
        on_stop: Callable[
            [],
            None
        ],
        register_key: str = "h",
        execute_key: str = "s",
    ) -> None:

        self.on_register = (
            on_register
        )

        self.on_execute = (
            on_execute
        )

        self.on_stop = (
            on_stop
        )

        self.register_key = (
            register_key.lower()
        )

        self.execute_key = (
            execute_key.lower()
        )

        self._listener: (
            keyboard.Listener | None
        ) = None

    def start(self) -> None:

        if (
            self._listener
            is not None
        ):

            return

        self._listener = (
            keyboard.Listener(
                on_press=self._on_press
            )
        )

        self._listener.start()

    def stop(self) -> None:

        if (
            self._listener
            is not None
        ):

            self._listener.stop()

            self._listener = None

    def _on_press(
        self,
        key:
        keyboard.Key
        | keyboard.KeyCode
    ) -> None:

        try:

            char = key.char

            if char is None:
                return

            char = char.lower()

            if (
                char
                == self.register_key
            ):

                self.on_register()

            elif (
                char
                == self.execute_key
            ):

                self.on_execute()

        except AttributeError:

            if (
                key
                == keyboard.Key.esc
            ):

                self.on_stop()