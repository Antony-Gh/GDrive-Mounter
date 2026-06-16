import subprocess


class MountManager:

    def __init__(
        self,
        rclone_path
    ):

        self.rclone = rclone_path

    def mount(
        self,
        folder_id,
        drive_letter
    ):

        cmd = [

            self.rclone,

            "mount",

            f":drive,root_folder_id={folder_id}:",

            f"{drive_letter}:",

            "--vfs-cache-mode",
            "full",

            "--network-mode"
        ]

        return subprocess.Popen(cmd)

    def unmount(
        self,
        drive_letter
    ):

        subprocess.run(
            [
                "taskkill",
                "/F",
                "/IM",
                "rclone.exe"
            ]
        )