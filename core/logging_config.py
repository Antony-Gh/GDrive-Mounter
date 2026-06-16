import logging
from pathlib import Path

from constants import LOG_FILE


class GUILogHandler(logging.Handler):

    def __init__(self, callback):

        super().__init__()

        self.callback = callback

    def emit(self, record):

        try:
            self.callback(
                self.format(record)
            )
        except Exception:
            self.handleError(record)


def _formatter():

    return logging.Formatter(
        "%(asctime)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )


def setup_logging(gui_callback=None):

    log_path = Path(LOG_FILE)

    log_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    root = logging.getLogger()
    root.setLevel(logging.INFO)

    if not any(
        isinstance(
            handler,
            logging.FileHandler
        )
        for handler in root.handlers
    ):
        file_handler = logging.FileHandler(
            log_path,
            encoding="utf8"
        )
        file_handler.setFormatter(
            _formatter()
        )
        root.addHandler(file_handler)

    if gui_callback:
        add_gui_handler(gui_callback)

    return root


def add_gui_handler(gui_callback):

    root = logging.getLogger()

    if any(
        isinstance(
            handler,
            GUILogHandler
        )
        for handler in root.handlers
    ):
        return root

    gui_handler = GUILogHandler(
        gui_callback
    )
    gui_handler.setFormatter(
        _formatter()
    )
    root.addHandler(gui_handler)

    return root
