import logging
import subprocess

from core.remote_manager import RemoteManager

logger = logging.getLogger(__name__)


class AuthManager:

    def __init__(
        self,
        rclone_exe
    ):

        self.rclone = rclone_exe
        self.remote_manager = RemoteManager(
            rclone_exe
        )

    def remote_exists(
        self,
        remote_name
    ):

        return self.remote_manager.remote_exists(
            remote_name
        )

    def is_authenticated(
        self,
        remote_name
    ):

        if not self.remote_exists(
            remote_name
        ):
            return False

        result = subprocess.run(
            [
                self.rclone,
                "about",
                f"{remote_name}:"
            ],
            capture_output=True,
            text=True
        )

        return result.returncode == 0

    def skip_authentication(
        self,
        remote_name
    ):

        logger.info(
            "Remote '%s' is already "
            "authenticated.",
            remote_name
        )

    def launch_authentication(
        self,
        remote_name
    ):

        logger.info(
            "Launching OAuth for "
            "remote '%s'.",
            remote_name
        )

        if self.remote_exists(
            remote_name
        ):
            subprocess.Popen(
                [
                    "cmd",
                    "/c",
                    "start",
                    "Rclone OAuth",
                    "cmd",
                    "/k",
                    self.rclone,
                    "config",
                    "reconnect",
                    f"{remote_name}:"
                ]
            )
        else:
            subprocess.Popen(
                [
                    "cmd",
                    "/c",
                    "start",
                    "Rclone OAuth",
                    "cmd",
                    "/k",
                    self.rclone,
                    "authorize",
                    "drive"
                ]
            )

    def ensure_remote_ready(
        self,
        remote_name,
        folder_id
    ):

        self.remote_manager.ensure_remote(
            remote_name,
            folder_id
        )

        if self.is_authenticated(
            remote_name
        ):
            self.skip_authentication(
                remote_name
            )
            return True

        self.launch_authentication(
            remote_name
        )
        return False

    def authenticate(
        self,
        remote_name,
        folder_id
    ):

        self.remote_manager.ensure_remote(
            remote_name,
            folder_id
        )

        if self.is_authenticated(
            remote_name
        ):
            self.skip_authentication(
                remote_name
            )
            return True

        self.launch_authentication(
            remote_name
        )
        return False
