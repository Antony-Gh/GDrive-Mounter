import logging
import subprocess

import requests

from constants import DEFAULT_RC_PORT

logger = logging.getLogger(__name__)


class MountManager:

    def __init__(
        self,
        rclone_exe,
        rc_port=DEFAULT_RC_PORT
    ):

        self.rclone = rclone_exe
        self.rc_port = rc_port
        self.process = None
        self.remote_name = None
        self.drive_letter = None
        self.attached_pid = None

    @property
    def rc_url(self):

        return (
            f"http://127.0.0.1:"
            f"{self.rc_port}"
        )

    def mount(
        self,
        remote_name,
        drive_letter
    ):

        self.remote_name = remote_name
        self.drive_letter = drive_letter

        command = [
            self.rclone,
            "mount",
            f"{remote_name}:",
            f"{drive_letter}:",
            "--vfs-cache-mode",
            "full",
            "--network-mode",
            "--dir-cache-time",
            "72h",
            "--rc",
            "--rc-addr",
            f"localhost:{self.rc_port}",
            "--rc-no-auth",
        ]

        logger.info(
            "Mounting %s: on %s:",
            remote_name,
            drive_letter
        )

        self.process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        return self.process

    def _rc_call(
        self,
        endpoint,
        payload=None
    ):

        response = requests.post(
            f"{self.rc_url}/{endpoint}",
            json=payload or {},
            timeout=1
        )
        response.raise_for_status()
        return response.json()

    def get_core_stats(self):

        try:
            return self._rc_call(
                "core/stats"
            )
        except Exception as ex:
            logger.debug(
                "RC core/stats failed: %s",
                ex
            )
            return None

    def get_vfs_stats(self):

        try:
            return self._rc_call(
                "vfs/stats"
            )
        except Exception as ex:
            logger.debug(
                "RC vfs/stats failed: %s",
                ex
            )
            return None

    def get_stats_summary(self):

        if not self.is_process_alive():
            return {
                "mounted": False,
                "speed": "0 B/s",
                "transfers": 0,
                "cache": "0 B"
            }

        core = self.get_core_stats() or {}
        vfs = self.get_vfs_stats() or {}

        speed = core.get(
            "speed",
            0.0
        )
        transfers = core.get(
            "transfers",
            0
        )
        cache_entries = vfs.get(
            "diskCache",
            {}
        ).get(
            "files",
            0
        )

        return {
            "mounted": True,
            "speed": self._format_bytes(
                speed
            ) + "/s",
            "transfers": transfers,
            "cache": f"{cache_entries} files"
        }

    @staticmethod
    def _format_bytes(value):

        units = [
            "B",
            "KiB",
            "MiB",
            "GiB",
        ]
        size = float(value)

        for unit in units:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024

        return f"{size:.1f} TiB"

    def is_process_alive(self):

        if (
            self.process is not None
            and self.process.poll() is None
        ):
            return True

        if self.attached_pid:
            from core.mount_session import (
                MountSessionStore,
            )
            return MountSessionStore.is_process_running(
                self.attached_pid
            )

        return False

    def is_running(self):

        if self.is_process_alive():
            return True

        return self.get_core_stats() is not None

    def unmount(self):

        mount_point = None

        if self.drive_letter:
            mount_point = (
                f"{self.drive_letter}:"
            )

        if mount_point:
            try:
                self._rc_call(
                    "mount/unmount",
                    {
                        "mountPoint": mount_point
                    }
                )
                logger.info(
                    "Unmount requested via RC."
                )
            except Exception:
                logger.warning(
                    "RC unmount failed."
                )

        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.process.kill()
            except Exception:
                pass
        elif self.attached_pid:
            subprocess.run(
                [
                    "taskkill",
                    "/PID",
                    str(self.attached_pid),
                    "/F",
                ],
                capture_output=True,
            )

        self.process = None
        self.attached_pid = None
        self.remote_name = None
        self.drive_letter = None

    def attach_session(self, session):

        self.remote_name = session.remote_name
        self.drive_letter = session.drive_letter
        self.rc_port = session.rc_port
        self.attached_pid = session.pid
