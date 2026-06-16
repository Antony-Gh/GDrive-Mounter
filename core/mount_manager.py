import subprocess


class MountManager:

    def __init__(
        self,
        rclone_exe
    ):

        self.rclone = rclone_exe

        self.process = None

    def mount(
        self,
        folder_id,
        drive_letter
    ):

        command = [

            self.rclone,

            "mount",

            (
                f":drive,"
                f"root_folder_id="
                f"{folder_id}:"
            ),

            f"{drive_letter}:",

            "--vfs-cache-mode",
            "full",

            "--network-mode",

            "--dir-cache-time",
            "72h"
        ]

        self.process = subprocess.Popen(
            command
        )

        return self.process

    def unmount(self):

        if self.process:

            self.process.terminate()

            self.process = None