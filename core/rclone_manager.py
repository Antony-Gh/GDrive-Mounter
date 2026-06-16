import logging
import shutil
import zipfile
import subprocess
from pathlib import Path

import requests

from constants import RCLONE_API, RCLONE_DIR

logger = logging.getLogger(__name__)


class RcloneManager:

    def __init__(
        self,
        tools_dir=RCLONE_DIR
    ):

        self.tools_dir = Path(tools_dir)

        self.tools_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        self.rclone_exe = None

    @property
    def stable_exe(self):

        return self.tools_dir / "rclone.exe"

    def find_in_tools(self):

        if self.stable_exe.exists():
            self.rclone_exe = str(
                self.stable_exe
            )
            return self.rclone_exe

        for path in self.tools_dir.rglob(
            "rclone.exe"
        ):
            self.rclone_exe = str(path)
            return self.rclone_exe

        return None

    def find_existing(self):

        found = self.find_in_tools()

        if found:
            return found

        exe = shutil.which("rclone")

        if exe:
            logger.info(
                "Using system rclone: %s",
                exe,
            )
            self.rclone_exe = exe
            return exe

        return None

    def _pick_asset(self, release):

        assets = release.get("assets", [])

        for asset in assets:
            name = asset.get("name", "")

            if "windows-amd64.zip" in name:
                return (
                    asset[
                        "browser_download_url"
                    ],
                    name,
                )

        return None, None

    def download_latest(self):

        response = requests.get(
            RCLONE_API,
            timeout=30,
            headers={
                "Accept": (
                    "application/vnd.github+json"
                ),
                "User-Agent": "GDrive-Mounter",
            },
        )

        response.raise_for_status()

        release = response.json()
        asset_url, asset_name = (
            self._pick_asset(release)
        )

        if not asset_url:
            raise RuntimeError(
                "Unable to find Windows release"
            )

        zip_path = (
            self.tools_dir.parent
            / asset_name
        )

        logger.info(
            "Downloading rclone to %s",
            zip_path,
        )

        with requests.get(
            asset_url,
            stream=True,
            timeout=120,
            headers={
                "User-Agent": "GDrive-Mounter",
            },
        ) as download:

            download.raise_for_status()

            with open(
                zip_path,
                "wb"
            ) as file:
                for chunk in download.iter_content(
                    8192
                ):
                    if chunk:
                        file.write(chunk)

        logger.info(
            "Extracting rclone into %s",
            self.tools_dir,
        )

        with zipfile.ZipFile(
            zip_path,
            "r"
        ) as archive:
            archive.extractall(
                self.tools_dir
            )

        found = self.find_in_tools()

        if not found:
            raise RuntimeError(
                "rclone.exe not found after extraction"
            )

        if Path(found) != self.stable_exe:
            shutil.copy2(
                found,
                self.stable_exe
            )
            self.rclone_exe = str(
                self.stable_exe
            )
            logger.info(
                "Copied rclone.exe to %s",
                self.stable_exe,
            )

        return self.rclone_exe

    def ensure(self):

        found = self.find_in_tools()

        if found:
            logger.info(
                "Rclone is already installed: %s",
                found,
            )
            return found

        return self.download_latest()

    def list_remotes(self):

        exe = self.ensure()

        output = subprocess.check_output(
            [
                exe,
                "listremotes",
            ],
            text=True,
        )

        return [
            line.replace(":", "").strip()
            for line in output.splitlines()
            if line.strip()
        ]

    def version(self):

        exe = self.ensure()

        return subprocess.check_output(
            [
                exe,
                "version",
            ],
            text=True,
        )
