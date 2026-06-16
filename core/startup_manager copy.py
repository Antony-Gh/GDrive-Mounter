import os
from pathlib import Path


class StartupManager:

    @staticmethod
    def startup_folder():

        return Path(
            os.environ["APPDATA"]
        ) / \
            "Microsoft" / \
            "Windows" / \
            "Start Menu" / \
            "Programs" / \
            "Startup"