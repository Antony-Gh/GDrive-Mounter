import logging
import threading

from PIL import Image, ImageDraw
import pystray


logger = logging.getLogger(__name__)


class TrayManager:

    def __init__(
        self,
        app,
        on_show,
        on_mount,
        on_unmount,
        on_open_drive,
        on_exit
    ):

        self.app = app
        self.on_show = on_show
        self.on_mount = on_mount
        self.on_unmount = on_unmount
        self.on_open_drive = on_open_drive
        self.on_exit = on_exit
        self.icon = None
        self.thread = None

    @staticmethod
    def _create_image():

        image = Image.new(
            "RGB",
            (64, 64),
            color=(66, 133, 244)
        )
        draw = ImageDraw.Draw(image)
        draw.rectangle(
            (8, 8, 56, 56),
            fill=(255, 255, 255)
        )
        draw.rectangle(
            (16, 20, 48, 44),
            fill=(66, 133, 244)
        )
        return image

    def start(self):

        menu = pystray.Menu(
            pystray.MenuItem(
                "Show",
                lambda icon, item: self.on_show()
            ),
            pystray.MenuItem(
                "Mount",
                lambda icon, item: self.on_mount()
            ),
            pystray.MenuItem(
                "Unmount",
                lambda icon, item: self.on_unmount()
            ),
            pystray.MenuItem(
                "Open Drive",
                lambda icon, item: self.on_open_drive()
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                "Exit",
                lambda icon, item: self.on_exit()
            ),
        )

        self.icon = pystray.Icon(
            "gdrive_mounter",
            self._create_image(),
            "Google Drive Folder Mounter",
            menu
        )

        self.thread = threading.Thread(
            target=self.icon.run,
            daemon=True
        )
        self.thread.start()
        logger.info(
            "System tray started."
        )

    def stop(self):

        if self.icon:
            self.icon.stop()
            self.icon = None
