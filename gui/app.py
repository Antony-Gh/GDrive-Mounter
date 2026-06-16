import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkinter import scrolledtext
import logging
import threading
import os
import sys
import webbrowser
from pathlib import Path

from config import ConfigManager
from constants import CURRENT_VERSION

from core.drive_parser import DriveParser
from core.rclone_manager import RcloneManager
from core.winfsp_manager import WinFspManager
from core.mount_manager import MountManager
from core.startup_manager import StartupManager
from core.auth_manager import AuthManager
from core.remote_manager import RemoteManager
from core.mount_session import (
    MountSession,
    MountSessionStore,
)
from core.updater import Updater
from gui.tray_manager import TrayManager


logger = logging.getLogger(__name__)


class App(tk.Tk):

    def __init__(self):

        super().__init__()

        self.title(
            f"Google Drive Folder Mounter "
            f"v{CURRENT_VERSION}"
        )

        self.geometry(
            "900x750"
        )

        self.config_data = (
            ConfigManager.load()
        )

        self.rclone = RcloneManager()
        self.winfsp = WinFspManager()
        self.mount_manager = None
        self.auth_manager = None
        self.remote_manager = None
        self.mount_process = None
        self.mounting = False
        self.session_store = MountSessionStore()
        self.tray = None
        self.stats_job = None
        self.startup_batch_file = (
            Path(__file__).resolve().parent.parent /
            "mount_on_startup.bat"
        )

        self.protocol(
            "WM_DELETE_WINDOW",
            self.on_close
        )

        self.create_ui()
        self.load_settings()
        self.apply_theme()
        self.restore_mount_session()
        self.check_for_updates()
        self.start_tray()

    def create_ui(self):

        main = ttk.Frame(
            self,
            padding=20
        )

        main.pack(
            fill="both",
            expand=True
        )

        ttk.Label(
            main,
            text="Remote Name"
        ).grid(
            row=0,
            column=0,
            sticky="w"
        )

        self.remote_var = tk.StringVar()

        ttk.Entry(
            main,
            textvariable=self.remote_var,
            width=50
        ).grid(
            row=0,
            column=1,
            sticky="ew"
        )

        ttk.Label(
            main,
            text="Folder URL / ID"
        ).grid(
            row=1,
            column=0,
            sticky="w"
        )

        self.folder_var = tk.StringVar()

        ttk.Entry(
            main,
            textvariable=self.folder_var,
            width=50
        ).grid(
            row=1,
            column=1,
            sticky="ew"
        )

        ttk.Label(
            main,
            text="Drive Letter"
        ).grid(
            row=2,
            column=0,
            sticky="w"
        )

        self.drive_var = tk.StringVar()

        ttk.Entry(
            main,
            textvariable=self.drive_var,
            width=10
        ).grid(
            row=2,
            column=1,
            sticky="w"
        )

        stats = ttk.LabelFrame(
            main,
            text="Mount Status",
            padding=10
        )
        stats.grid(
            row=3,
            column=0,
            columnspan=2,
            sticky="ew",
            pady=(10, 0)
        )

        self.status_var = tk.StringVar(
            value="Unmounted"
        )
        self.speed_var = tk.StringVar(
            value="0 B/s"
        )
        self.transfers_var = tk.StringVar(
            value="0"
        )
        self.cache_var = tk.StringVar(
            value="0 files"
        )

        ttk.Label(
            stats,
            text="State:"
        ).grid(
            row=0,
            column=0,
            sticky="w"
        )
        ttk.Label(
            stats,
            textvariable=self.status_var
        ).grid(
            row=0,
            column=1,
            sticky="w",
            padx=(8, 20)
        )

        ttk.Label(
            stats,
            text="Speed:"
        ).grid(
            row=0,
            column=2,
            sticky="w"
        )
        ttk.Label(
            stats,
            textvariable=self.speed_var
        ).grid(
            row=0,
            column=3,
            sticky="w",
            padx=(8, 20)
        )

        ttk.Label(
            stats,
            text="Transfers:"
        ).grid(
            row=1,
            column=0,
            sticky="w"
        )
        ttk.Label(
            stats,
            textvariable=self.transfers_var
        ).grid(
            row=1,
            column=1,
            sticky="w",
            padx=(8, 20)
        )

        ttk.Label(
            stats,
            text="Cache:"
        ).grid(
            row=1,
            column=2,
            sticky="w"
        )
        ttk.Label(
            stats,
            textvariable=self.cache_var
        ).grid(
            row=1,
            column=3,
            sticky="w",
            padx=(8, 20)
        )

        button_frame = ttk.Frame(main)

        button_frame.grid(
            row=4,
            column=0,
            columnspan=2,
            pady=20
        )

        ttk.Button(
            button_frame,
            text="Install Rclone",
            command=self.install_rclone
        ).pack(
            side="left",
            padx=5
        )

        ttk.Button(
            button_frame,
            text="Install WinFsp",
            command=self.install_winfsp
        ).pack(
            side="left",
            padx=5
        )

        ttk.Button(
            button_frame,
            text="Authenticate",
            command=self.authenticate
        ).pack(
            side="left",
            padx=5
        )

        ttk.Button(
            button_frame,
            text="Mount",
            command=self.mount
        ).pack(
            side="left",
            padx=5
        )

        ttk.Button(
            button_frame,
            text="Unmount",
            command=self.unmount
        ).pack(
            side="left",
            padx=5
        )

        ttk.Button(
            button_frame,
            text="Open Folder",
            command=self.open_folder
        ).pack(
            side="left",
            padx=5
        )

        self.startup_var = tk.BooleanVar()

        ttk.Checkbutton(
            main,
            text="Mount at startup",
            variable=self.startup_var
        ).grid(
            row=5,
            column=0,
            sticky="w"
        )

        ttk.Button(
            main,
            text="Save Settings",
            command=self.save_settings
        ).grid(
            row=5,
            column=1,
            sticky="e"
        )

        self.log = scrolledtext.ScrolledText(
            main,
            height=22
        )

        self.log.grid(
            row=6,
            column=0,
            columnspan=2,
            sticky="nsew"
        )

        main.columnconfigure(1, weight=1)
        main.rowconfigure(6, weight=1)

    def apply_theme(self):

        try:
            import sv_ttk
            sv_ttk.set_theme("dark")
            logger.info("Dark theme enabled.")
        except Exception:
            logger.info("Default theme in use.")

    def write_log(self, text):

        def append():
            self.log.insert(
                tk.END,
                text + "\n"
            )
            self.log.see(tk.END)

        self.after(0, append)

    def ensure_managers(self):

        exe = self.rclone.ensure()

        if not self.auth_manager:
            self.auth_manager = AuthManager(exe)

        if not self.remote_manager:
            self.remote_manager = RemoteManager(exe)

        if not self.mount_manager:
            self.mount_manager = MountManager(exe)

        return exe

    def normalized_drive(self):

        drive = (
            self.drive_var.get()
            .strip()
            .upper()
            .replace(":", "")
        )

        if not drive:
            raise ValueError(
                "Drive letter is required."
            )

        if len(drive) != 1 or not drive.isalpha():
            raise ValueError(
                "Drive letter must be a single "
                "letter (A-Z)."
            )

        return drive

    def remote_name(self):

        name = self.remote_var.get().strip()

        if not name:
            raise ValueError(
                "Remote name is required."
            )

        return name

    def create_startup_batch(self):

        if getattr(sys, "frozen", False):
            launcher = (
                f'"{Path(sys.executable)}"'
            )
        else:
            launcher = (
                f'"{sys.executable}" '
                f'"{Path(__file__).resolve().parent.parent / "main.py"}"'
            )

        self.startup_batch_file.write_text(
            "@echo off\n"
            "cd /d \"%~dp0\"\n"
            f"start \"\" {launcher}\n",
            encoding="utf8"
        )

    def apply_startup_setting(self):

        self.create_startup_batch()

        if self.startup_var.get():
            StartupManager.add_batch(
                str(self.startup_batch_file)
            )
            logger.info("Startup enabled.")
        else:
            StartupManager.remove_batch(
                str(self.startup_batch_file)
            )
            logger.info("Startup disabled.")

    def restore_mount_session(self):

        session = (
            self.session_store.load_active()
        )

        if not session:
            return

        try:
            self.ensure_managers()
            self.mount_manager.attach_session(
                session
            )
            self.mounting = True
            self.remote_var.set(
                session.remote_name
            )
            self.drive_var.set(
                session.drive_letter
            )
            logger.info(
                "Reconnected to active mount "
                "(pid=%s).",
                session.pid
            )
            self.start_stats_polling()
        except Exception as ex:
            logger.warning(
                "Could not restore mount "
                "session: %s",
                ex
            )
            self.session_store.clear()

    def start_stats_polling(self):

        if self.stats_job:
            self.after_cancel(self.stats_job)

        self.poll_stats()

    def stop_stats_polling(self):

        if self.stats_job:
            self.after_cancel(self.stats_job)
            self.stats_job = None

        self.status_var.set("Unmounted")
        self.speed_var.set("0 B/s")
        self.transfers_var.set("0")
        self.cache_var.set("0 files")

    def poll_stats(self):

        if (
            self.mount_manager
            and self.mount_manager.is_running()
        ):
            summary = (
                self.mount_manager
                .get_stats_summary()
            )
            self.status_var.set(
                "Mounted"
                if summary["mounted"]
                else "Unmounted"
            )
            self.speed_var.set(summary["speed"])
            self.transfers_var.set(
                str(summary["transfers"])
            )
            self.cache_var.set(summary["cache"])
        else:
            if self.mounting:
                self.mounting = False
                self.session_store.clear()
            self.stop_stats_polling()
            return

        self.stats_job = self.after(
            2000,
            self.poll_stats
        )

    def stream_mount_logs(self):

        if not self.mount_process:
            return

        stream = self.mount_process.stdout

        if not stream:
            return

        for line in stream:
            line = line.strip()
            if line:
                logger.info("[rclone] %s", line)

        exit_code = self.mount_process.poll()
        self.mounting = False
        self.stop_stats_polling()

        if exit_code is None:
            logger.info(
                "Mount process finished."
            )
        elif exit_code == 0:
            logger.info(
                "Mount process exited cleanly."
            )
        else:
            logger.warning(
                "Mount process exited with "
                "code %s.",
                exit_code
            )

        self.session_store.clear()

    def install_rclone(self):

        def task():
            try:
                logger.info("Installing rclone...")
                exe = self.rclone.ensure()
                logger.info("Installed: %s", exe)
            except Exception as ex:
                logger.error(
                    "Rclone install failed: %s",
                    ex
                )
                self.after(
                    0,
                    lambda: messagebox.showerror(
                        "Rclone Error",
                        str(ex)
                    )
                )

        threading.Thread(
            target=task,
            daemon=True
        ).start()

    def install_winfsp(self):

        def task():
            try:
                if self.winfsp.is_installed():
                    logger.info(
                        "WinFsp is already "
                        "installed."
                    )
                    return

                logger.info("Installing WinFsp...")
                self.winfsp.install()
                logger.info(
                    "WinFsp installer launched."
                )
            except Exception as ex:
                logger.error(
                    "WinFsp install failed: %s",
                    ex
                )
                self.after(
                    0,
                    lambda: messagebox.showerror(
                        "WinFsp Error",
                        str(ex)
                    )
                )

        threading.Thread(
            target=task,
            daemon=True
        ).start()

    def authenticate(self):

        def task():
            try:
                self.ensure_managers()

                folder_id = (
                    DriveParser.extract_folder_id(
                        self.folder_var.get()
                    )
                )
                name = self.remote_name()

                ready = (
                    self.auth_manager.authenticate(
                        name,
                        folder_id
                    )
                )

                if ready:
                    logger.info(
                        "Authentication verified."
                    )
                else:
                    logger.info(
                        "Complete OAuth in the "
                        "opened window, then "
                        "mount again."
                    )
            except Exception as ex:
                logger.error(
                    "Authentication failed: %s",
                    ex
                )
                self.after(
                    0,
                    lambda: messagebox.showerror(
                        "Authentication Error",
                        str(ex)
                    )
                )

        threading.Thread(
            target=task,
            daemon=True
        ).start()

    def mount(self):

        if self.mounting:
            logger.info(
                "Mount is already running."
            )
            return

        def task():
            try:
                self.ensure_managers()

                if not self.winfsp.is_installed():
                    raise RuntimeError(
                        "WinFsp is not installed."
                    )

                folder_id = (
                    DriveParser.extract_folder_id(
                        self.folder_var.get()
                    )
                )
                drive_letter = (
                    self.normalized_drive()
                )
                name = self.remote_name()

                if not self.auth_manager.ensure_remote_ready(
                    name,
                    folder_id
                ):
                    logger.info(
                        "Authenticate before "
                        "mounting."
                    )
                    return

                self.mount_process = (
                    self.mount_manager.mount(
                        name,
                        drive_letter
                    )
                )
                self.mounting = True

                session = MountSession.start(
                    self.mount_process.pid,
                    name,
                    drive_letter,
                    self.mount_manager.rc_port
                )
                self.session_store.save(session)

                logger.info(
                    "Mounted %s: on %s:",
                    name,
                    drive_letter
                )

                self.after(
                    0,
                    self.start_stats_polling
                )
                self.stream_mount_logs()

            except Exception as ex:
                self.mounting = False
                logger.error(
                    "Mount failed: %s",
                    ex
                )
                self.after(
                    0,
                    lambda: messagebox.showerror(
                        "Mount Error",
                        str(ex)
                    )
                )

        threading.Thread(
            target=task,
            daemon=True
        ).start()

    def unmount(self):

        if not self.mount_manager:
            logger.info("Nothing to unmount.")
            return

        self.mount_manager.unmount()
        self.mounting = False
        self.mount_process = None
        self.session_store.clear()
        self.stop_stats_polling()
        logger.info("Unmounted.")

    def open_folder(self):

        try:
            drive = (
                self.normalized_drive()
                + ":\\"
            )

            if not os.path.exists(drive):
                raise FileNotFoundError(
                    f"{drive} is not available."
                )

            os.startfile(drive)
        except Exception as ex:
            logger.error(
                "Open folder failed: %s",
                ex
            )
            messagebox.showerror(
                "Open Folder Error",
                str(ex)
            )

    def save_settings(self):

        data = {
            "remote_name": self.remote_var.get(),
            "folder_id": self.folder_var.get(),
            "drive_letter": self.drive_var.get(),
            "mount_on_startup": (
                self.startup_var.get()
            ),
        }

        ConfigManager.save(data)

        try:
            self.apply_startup_setting()
        except Exception as ex:
            logger.error(
                "Startup update failed: %s",
                ex
            )
            messagebox.showerror(
                "Startup Error",
                str(ex)
            )
            return

        logger.info("Settings saved.")

    def load_settings(self):

        self.remote_var.set(
            self.config_data.get(
                "remote_name",
                ""
            )
        )
        self.folder_var.set(
            self.config_data.get(
                "folder_id",
                ""
            )
        )
        self.drive_var.set(
            self.config_data.get(
                "drive_letter",
                "X"
            )
        )
        self.startup_var.set(
            self.config_data.get(
                "mount_on_startup",
                False
            )
        )

    def check_for_updates(self):

        def task():
            result = Updater.check_quietly()

            if not result:
                return

            if result["update_available"]:
                message = (
                    "Update available: "
                    f"{result['latest_version']} "
                    f"(current "
                    f"{result['current_version']})"
                )
                logger.info(message)
                self.after(
                    0,
                    lambda: messagebox.showinfo(
                        "Update Available",
                        message,
                        parent=self
                    )
                )

                url = result.get("url")
                if url:
                    webbrowser.open(url)

        threading.Thread(
            target=task,
            daemon=True
        ).start()

    def start_tray(self):

        self.tray = TrayManager(
            self,
            on_show=self.show_window,
            on_mount=self.mount,
            on_unmount=self.unmount,
            on_open_drive=self.open_folder,
            on_exit=self.exit_app
        )
        self.tray.start()

    def show_window(self):

        self.after(0, self.deiconify)
        self.after(0, self.lift)

    def on_close(self):

        self.withdraw()

    def exit_app(self):

        if self.mount_manager:
            self.mount_manager.unmount()

        if self.tray:
            self.tray.stop()

        self.destroy()
