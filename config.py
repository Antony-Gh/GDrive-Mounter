import json
from pathlib import Path

from constants import SETTINGS_FILE

DEFAULT_CONFIG = {
    "remote_name": "public-drive-folder",
    "folder_id": "",
    "drive_letter": "W",
    "rclone_path": "",
    "mount_on_startup": False
}


class ConfigManager:

    @staticmethod
    def load():

        file = Path(SETTINGS_FILE)

        if not file.exists():
            return DEFAULT_CONFIG.copy()

        with open(file, "r", encoding="utf8") as f:
            return json.load(f)

    @staticmethod
    def save(data):

        Path(SETTINGS_FILE).parent.mkdir(
            parents=True,
            exist_ok=True
        )

        with open(
            SETTINGS_FILE,
            "w",
            encoding="utf8"
        ) as f:

            json.dump(
                data,
                f,
                indent=4
            )