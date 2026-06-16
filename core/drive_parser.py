import re


class DriveParser:

    FOLDER_PATTERNS = [

        r"folders\/([a-zA-Z0-9_-]+)",

        r"id=([a-zA-Z0-9_-]+)",

        r"^([a-zA-Z0-9_-]{20,})$"
    ]

    @classmethod
    def extract_folder_id(cls, value):

        value = value.strip()

        for pattern in cls.FOLDER_PATTERNS:

            match = re.search(
                pattern,
                value
            )

            if match:
                return match.group(1)

        raise ValueError(
            "Unable to extract Google Drive folder ID"
        )