import logging
import subprocess
import winreg
from pathlib import Path

import requests

from constants import (
    WINFSP_API,
    WINFSP_URL,
)

logger = logging.getLogger(__name__)


class WinFspManager:

    REGISTRY_PATH = r"SOFTWARE\WinFsp"

    INSTALLER_DIR = Path("tools")

    def is_installed(self):

        # 1) Try 64‑bit and 32‑bit registry views
        for view_flag in (
            0,
            winreg.KEY_WOW64_64KEY,
            winreg.KEY_WOW64_32KEY,
        ):

            try:
                access = winreg.KEY_READ | view_flag
                winreg.OpenKey(
                    winreg.HKEY_LOCAL_MACHINE,
                    self.REGISTRY_PATH,
                    0,
                    access,
                )
                return True
            except FileNotFoundError:
                continue
            except OSError:
                continue

        # 2) Fallback to detecting WinFsp CLI tool
        try:
            result = subprocess.run(
                [
                    "where",
                    "fsptool-x64.exe",
                ],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                return True
        except Exception:
            pass

        return False

    def find_local_installer(self):

        if not self.INSTALLER_DIR.exists():
            return None

        installers = sorted(
            self.INSTALLER_DIR.glob("winfsp*.msi"),
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        )

        if installers:
            return installers[0]

        legacy = self.INSTALLER_DIR / "winfsp.msi"
        if legacy.exists():
            return legacy

        return None

    def resolve_download_url(self):

        try:
            response = requests.get(
                WINFSP_API,
                timeout=30,
                headers={
                    "Accept": (
                        "application/vnd.github+json"
                    ),
                    "User-Agent": (
                        "GDrive-Mounter"
                    ),
                },
            )
            response.raise_for_status()

            release = response.json()

            for asset in release.get(
                "assets",
                []
            ):
                name = asset.get("name", "")

                if (
                    name.endswith(".msi")
                    and "winfsp" in name.lower()
                ):
                    return (
                        asset[
                            "browser_download_url"
                        ],
                        name,
                    )

        except Exception as ex:
            logger.warning(
                "WinFsp GitHub lookup failed: %s",
                ex
            )

        return (
            WINFSP_URL,
            "winfsp.msi",
        )

    def download(self):

        local = self.find_local_installer()

        if local:
            logger.info(
                "Using bundled WinFsp installer: %s",
                local,
            )
            return local

        url, filename = self.resolve_download_url()

        installer = (
            self.INSTALLER_DIR / filename
        )

        installer.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        logger.info(
            "Downloading WinFsp from %s",
            url,
        )

        with requests.get(
            url,
            stream=True,
            timeout=120,
            allow_redirects=True,
            headers={
                "User-Agent": "GDrive-Mounter",
            },
        ) as response:

            response.raise_for_status()

            with open(
                installer,
                "wb"
            ) as file:
                for chunk in response.iter_content(
                    8192
                ):
                    if chunk:
                        file.write(chunk)

        logger.info(
            "Saved WinFsp installer to %s",
            installer,
        )

        return installer

    def install(self):

        if self.is_installed():
            logger.info(
                "WinFsp is already installed."
            )
            return

        installer = self.download()

        logger.info(
            "Launching WinFsp installer: %s",
            installer,
        )

        subprocess.Popen(
            [
                "msiexec",
                "/i",
                str(installer),
            ]
        )
