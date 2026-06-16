import subprocess
from pathlib import Path

import requests


class WinFspManager:

    URL = (
        "https://winfsp.dev/rel/"
        "winfsp-latest.msi"
    )

    def is_installed(self):

        try:

            result = subprocess.run(
                [
                    "where",
                    "fsptool-x64.exe"
                ],
                capture_output=True,
                text=True
            )

            return result.returncode == 0

        except Exception:

            return False

    def download(self):

        installer = Path(
            "tools/winfsp.msi"
        )

        installer.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        with requests.get(
            self.URL,
            stream=True
        ) as r:

            r.raise_for_status()

            with open(
                installer,
                "wb"
            ) as f:

                for chunk in r.iter_content(
                    8192
                ):
                    f.write(chunk)

        return installer

    def install(self):

        installer = self.download()

        subprocess.run(
            [
                "msiexec",
                "/i",
                str(installer)
            ]
        )