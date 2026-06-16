import subprocess
from pathlib import Path


class RcloneManager:

    def __init__(self, exe):

        self.exe = exe

    def version(self):

        return subprocess.check_output(
            [self.exe, "version"],
            text=True
        )

    def remotes(self):

        result = subprocess.check_output(
            [
                self.exe,
                "listremotes"
            ],
            text=True
        )

        return [
            line.replace(":", "")
            for line in result.splitlines()
        ]

    def authenticate(self):

        subprocess.run(
            [
                self.exe,
                "config"
            ]
        )