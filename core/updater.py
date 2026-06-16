import logging
import re

import requests

from constants import (
    APP_GITHUB_API,
    CURRENT_VERSION,
)

logger = logging.getLogger(__name__)


class Updater:

    @staticmethod
    def _parse_version(value):

        match = re.search(
            r"(\d+(?:\.\d+)*)",
            value or ""
        )

        if not match:
            return (0,)

        return tuple(
            int(part)
            for part in match.group(1).split(
                "."
            )
        )

    @classmethod
    def check_for_update(cls):

        response = requests.get(
            APP_GITHUB_API,
            timeout=20
        )
        response.raise_for_status()

        release = response.json()
        latest = release.get(
            "tag_name",
            ""
        ).lstrip("v")

        current = cls._parse_version(
            CURRENT_VERSION
        )
        remote = cls._parse_version(latest)

        if remote > current:
            return {
                "update_available": True,
                "current_version": (
                    CURRENT_VERSION
                ),
                "latest_version": latest,
                "url": release.get(
                    "html_url",
                    ""
                ),
            }

        return {
            "update_available": False,
            "current_version": CURRENT_VERSION,
            "latest_version": latest,
        }

    @classmethod
    def check_quietly(cls):

        try:
            return cls.check_for_update()
        except Exception as ex:
            logger.warning(
                "Update check failed: %s",
                ex
            )
            return None
