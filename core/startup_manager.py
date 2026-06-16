import os

from pathlib import Path


class StartupManager:

    @staticmethod
    def startup_dir():

        return Path(
            os.environ["APPDATA"]
        ) / \
        "Microsoft" / \
        "Windows" / \
        "Start Menu" / \
        "Programs" / \
        "Startup"

    @classmethod
    def add_batch(
        cls,
        bat_file
    ):

        startup = cls.startup_dir()

        shortcut = startup / (
            Path(bat_file).name
        )

        shortcut.write_text(
            (
                f'@echo off\n'
                f'call "{bat_file}"\n'
            )
        )

    @classmethod
    def remove_batch(
        cls,
        bat_file
    ):

        shortcut = cls.startup_dir() / (
            Path(bat_file).name
        )

        if shortcut.exists():
            shortcut.unlink()