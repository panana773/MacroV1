from __future__ import annotations

import json

from pathlib import Path
import sys

from typing import Any


DEFAULT_CONFIG: dict[
    str,
    Any
] = {

    "server_url": "",

    "target_time":
    "10:00:00.000",

    "click_interval_ms":
    30,

    "register_key":
    "h",

    "execute_key":
    "s",

    "click_queue":
    [],
}


class ConfigManager:
    def __init__(self) -> None:

        # PyInstaller one-file extracts source files to a temporary folder.
        # Keep user settings next to the executable instead.
        if getattr(sys, "frozen", False):
            project_root = Path(sys.executable).resolve().parent
        else:
            project_root = Path(__file__).resolve().parent.parent

        self.data_dir = (
            project_root
            / "data"
        )

        self.config_path = (
            self.data_dir
            / "settings.json"
        )

    def load(
        self
    ) -> dict[str, Any]:

        self.data_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        if not (
            self.config_path.exists()
        ):

            return (
                DEFAULT_CONFIG.copy()
            )

        try:

            with (
                self.config_path.open(
                    "r",
                    encoding="utf-8"
                )
            ) as file:

                loaded = (
                    json.load(file)
                )

        except (
            OSError,
            json.JSONDecodeError
        ):

            return (
                DEFAULT_CONFIG.copy()
            )

        config = (
            DEFAULT_CONFIG.copy()
        )

        if isinstance(
            loaded,
            dict
        ):

            config.update(
                loaded
            )

        return config

    def save(
        self,
        data: dict[str, Any]
    ) -> None:

        self.data_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        with (
            self.config_path.open(
                "w",
                encoding="utf-8"
            )
        ) as file:

            json.dump(
                data,
                file,
                ensure_ascii=False,
                indent=2
            )