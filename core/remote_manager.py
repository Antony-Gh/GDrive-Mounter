import subprocess


class RemoteManager:

    def __init__(
        self,
        rclone_exe
    ):

        self.rclone = rclone_exe

    def create_drive_remote(
        self,
        remote_name,
        folder_id
    ):

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

    def delete_remote(
        self,
        remote_name
    ):

        subprocess.run(
            [
                self.rclone,
                "config",
                "delete",
                remote_name
            ]
        )