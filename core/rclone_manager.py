import os
import shutil
import zipfile
import subprocess
from pathlib import Path

import requests


class RcloneManager:

    GITHUB_API = (
        "https://api.github.com/repos/"
        "rclone/rclone/releases/latest"
    )

    def __init__(self, tools_dir="tools"):

        self.tools_dir = Path(tools_dir)

        self.tools_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        self.rclone_exe = None

    def find_existing(self):

        exe = shutil.which("rclone")

        if exe:
            self.rclone_exe = exe
            return exe

        for path in self.tools_dir.rglob("rclone.exe"):

            self.rclone_exe = str(path)

            return str(path)

        return None

    def download_latest(self):

        response = requests.get(
            self.GITHUB_API,
            timeout=30
        )

        response.raise_for_status()

        release = response.json()

        asset_url = None

        for asset in release["assets"]:

            name = asset["name"]

            if (
                "windows-amd64.zip"
                in name
            ):
                asset_url = asset[
                    "browser_download_url"
                ]
                break

        if not asset_url:
            raise RuntimeError(
                "Unable to find Windows release"
            )

        zip_path = (
            self.tools_dir /
            "rclone.zip"
        )

        print(
            "Downloading rclone..."
        )

        with requests.get(
            asset_url,
            stream=True
        ) as r:

            r.raise_for_status()

            with open(
                zip_path,
                "wb"
            ) as f:

                for chunk in r.iter_content(
                    8192
                ):
                    f.write(chunk)

        extract_dir = (
            self.tools_dir /
            "rclone"
        )

        extract_dir.mkdir(
            exist_ok=True
        )

        with zipfile.ZipFile(
            zip_path,
            "r"
        ) as zip_ref:

            zip_ref.extractall(
                extract_dir
            )

        for exe in extract_dir.rglob(
            "rclone.exe"
        ):
            self.rclone_exe = str(exe)
            return str(exe)

        raise RuntimeError(
            "rclone.exe not found after extraction"
        )

    def ensure(self):

        found = self.find_existing()

        if found:
            return found

        return self.download_latest()

    def list_remotes(self):

        output = subprocess.check_output(
            [
                self.rclone_exe,
                "listremotes"
            ],
            text=True
        )

        return [
            x.replace(
                ":",
                ""
            )
            for x in output.splitlines()
        ]

    def version(self):

        return subprocess.check_output(
            [
                self.rclone_exe,
                "version"
            ],
            text=True
        )