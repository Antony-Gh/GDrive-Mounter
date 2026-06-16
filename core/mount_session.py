import json
import logging
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path

from constants import MOUNT_SESSION_FILE

logger = logging.getLogger(__name__)


@dataclass
class MountSession:

    pid: int
    remote_name: str
    drive_letter: str
    started_at: str
    rc_port: int = 5572

    @classmethod
    def start(
        cls,
        pid,
        remote_name,
        drive_letter,
        rc_port=5572
    ):

        return cls(
            pid=pid,
            remote_name=remote_name,
            drive_letter=drive_letter,
            started_at=datetime.now().isoformat(
                timespec="seconds"
            ),
            rc_port=rc_port
        )

    def to_dict(self):

        return asdict(self)

    @classmethod
    def from_dict(cls, data):

        return cls(**data)


class MountSessionStore:

    def __init__(
        self,
        path=MOUNT_SESSION_FILE
    ):

        self.path = Path(path)

    def save(self, session):

        self.path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        with open(
            self.path,
            "w",
            encoding="utf8"
        ) as f:
            json.dump(
                session.to_dict(),
                f,
                indent=4
            )

        logger.info(
            "Mount session saved (pid=%s).",
            session.pid
        )

    def load(self):

        if not self.path.exists():
            return None

        with open(
            self.path,
            "r",
            encoding="utf8"
        ) as f:
            data = json.load(f)

        return MountSession.from_dict(data)

    def clear(self):

        if self.path.exists():
            self.path.unlink()
            logger.info(
                "Mount session cleared."
            )

    @staticmethod
    def is_process_running(pid):

        if not pid:
            return False

        try:
            import ctypes

            PROCESS_QUERY_LIMITED_INFORMATION = (
                0x1000
            )
            handle = ctypes.windll.kernel32.OpenProcess(
                PROCESS_QUERY_LIMITED_INFORMATION,
                False,
                int(pid)
            )

            if not handle:
                return False

            ctypes.windll.kernel32.CloseHandle(
                handle
            )
            return True

        except Exception:
            return False

    def load_active(self):

        session = self.load()

        if not session:
            return None

        if self.is_process_running(
            session.pid
        ):
            return session

        logger.warning(
            "Stale mount session detected "
            "(pid=%s).",
            session.pid
        )
        self.clear()
        return None
