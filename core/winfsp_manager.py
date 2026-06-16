import logging
import subprocess
import winreg
from pathlib import Path

import requests

logger = logging.getLogger(__name__)


class WinFspManager:

    URL = (
        "https://winfsp.dev/rel/"
        "winfsp-latest.msi"
    )

    REGISTRY_PATH = r"SOFTWARE\WinFsp"

    def is_installed(self):

        try:
            winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                self.REGISTRY_PATH
            )
            return True
        except FileNotFoundError:
            return False
        except OSError:
            return False

    def download(self):

        installer = Path(
            "tools/winfsp.msi"
        )

        installer.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        logger.info(
            "Downloading WinFsp installer."
        )

        with requests.get(
            self.URL,
            stream=True,
            timeout=60
        ) as response:

            response.raise_for_status()

            with open(
                installer,
                "wb"
            ) as file:
                for chunk in response.iter_content(
                    8192
                ):
                    file.write(chunk)

        return installer

    def install(self):

        if self.is_installed():
            logger.info(
                "WinFsp is already installed."
            )
            return

        installer = self.download()

        subprocess.run(
            [
                "msiexec",
                "/i",
                str(installer)
            ]
        )
