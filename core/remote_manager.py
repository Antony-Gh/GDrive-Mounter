import json
import logging
import subprocess

logger = logging.getLogger(__name__)


class RemoteManager:

    def __init__(
        self,
        rclone_exe
    ):

        self.rclone = rclone_exe

    def list_remotes(self):

        output = subprocess.check_output(
            [
                self.rclone,
                "listremotes"
            ],
            text=True
        )

        return [
            line.replace(":", "").strip()
            for line in output.splitlines()
            if line.strip()
        ]

    def remote_exists(
        self,
        remote_name
    ):

        return remote_name in self.list_remotes()

    def get_remote_config(
        self,
        remote_name
    ):

        output = subprocess.check_output(
            [
                self.rclone,
                "config",
                "dump"
            ],
            text=True
        )

        config = json.loads(output)

        return config.get(remote_name, {})

    def get_folder_id(
        self,
        remote_name
    ):

        config = self.get_remote_config(
            remote_name
        )

        return config.get(
            "root_folder_id",
            ""
        )

    def create_remote(
        self,
        remote_name,
        folder_id
    ):

        logger.info(
            "Creating remote '%s'.",
            remote_name
        )

        subprocess.run(
            [
                self.rclone,
                "config",
                "create",
                remote_name,
                "drive",
                f"root_folder_id={folder_id}"
            ],
            check=True
        )

    def update_remote(
        self,
        remote_name,
        folder_id
    ):

        logger.info(
            "Updating remote '%s' "
            "folder ID.",
            remote_name
        )

        subprocess.run(
            [
                self.rclone,
                "config",
                "update",
                remote_name,
                "root_folder_id",
                folder_id
            ],
            check=True
        )

    def delete_remote(
        self,
        remote_name
    ):

        logger.info(
            "Deleting remote '%s'.",
            remote_name
        )

        subprocess.run(
            [
                self.rclone,
                "config",
                "delete",
                remote_name
            ],
            check=True
        )

    def ensure_remote(
        self,
        remote_name,
        folder_id
    ):

        if not self.remote_exists(
            remote_name
        ):
            self.create_remote(
                remote_name,
                folder_id
            )
            return

        current_id = self.get_folder_id(
            remote_name
        )

        if current_id != folder_id:
            self.update_remote(
                remote_name,
                folder_id
            )
