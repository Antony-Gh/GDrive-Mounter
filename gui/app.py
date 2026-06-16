import logging
import queue
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
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
from core.logging_config import add_gui_handler
from gui.theme import AppTheme


logger = logging.getLogger(__name__)

LOG_MAX_LINES = 300
STATS_POLL_MS = 5000
UI_POLL_MS = 100


class App(tk.Tk):

    def __init__(self):

        super().__init__()

        self.title(
            f"Google Drive Folder Mounter "
            f"v{CURRENT_VERSION}"
        )

        self.config_data = ConfigManager.load()

        self.rclone = RcloneManager()
        self.winfsp = WinFspManager()
        self.mount_manager = None
        self.auth_manager = None
        self.remote_manager = None
        self.mount_process = None
        self.mounting = False
        self.session_store = MountSessionStore()
        self.stats_job = None
        self._stats_polling = False
        self._shutting_down = False
        self._ui_queue = queue.SimpleQueue()
        self._log_pending = []
        self._last_stats = None
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
        add_gui_handler(self.write_log)
        logging.getLogger().setLevel(logging.INFO)
        self.write_log("Application started.")
        logging.getLogger().info(
            "Application ready."
        )
        self.after(0, self._drain_ui_queue)
        self.after(300, self._restore_mount_session_async)
        self.after(2000, self.check_for_updates)

    def post_ui(self, callback, *args, **kwargs):

        if self._shutting_down:
            return

        self._ui_queue.put(
            (callback, args, kwargs)
        )

    def _drain_ui_queue(self):

        if self._shutting_down:
            return

        while True:
            try:
                callback, args, kwargs = (
                    self._ui_queue.get_nowait()
                )
            except queue.Empty:
                break

            try:
                callback(*args, **kwargs)
            except tk.TclError:
                pass
            except Exception as ex:
                logger.debug(
                    "UI callback failed: %s",
                    ex
                )

        self.after(
            UI_POLL_MS,
            self._drain_ui_queue
        )

        if self._log_pending:
            self._flush_log_buffer()

    def create_ui(self):

        self.fonts = AppTheme.apply_root(self)
        AppTheme.build_header(self)

        container = tk.Frame(
            self,
            bg=AppTheme.BG,
        )
        container.pack(
            fill="both",
            expand=True,
            padx=28,
            pady=(0, 20),
        )

        self._canvas = tk.Canvas(
            container,
            bg=AppTheme.BG,
            highlightthickness=0,
            bd=0,
        )
        self._scrollbar = ttk.Scrollbar(
            container,
            orient="vertical",
            command=self._canvas.yview,
        )
        self._canvas.configure(
            yscrollcommand=self._scrollbar.set
        )

        self._scrollbar.pack(
            side="right",
            fill="y",
        )
        self._canvas.pack(
            side="left",
            fill="both",
            expand=True,
        )

        body = tk.Frame(
            self._canvas,
            bg=AppTheme.BG,
        )
        self._scroll_window = self._canvas.create_window(
            (0, 0),
            window=body,
            anchor="nw",
        )

        def _on_body_configure(event=None):
            self._canvas.configure(
                scrollregion=self._canvas.bbox("all")
            )

        def _on_canvas_configure(event):
            # keep inner content full width
            self._canvas.itemconfigure(
                self._scroll_window,
                width=event.width,
            )

        body.bind(
            "<Configure>",
            _on_body_configure,
        )
        self._canvas.bind(
            "<Configure>",
            _on_canvas_configure,
        )

        # mouse wheel scrolling (Windows)
        def _on_mousewheel(event):
            self._canvas.yview_scroll(
                int(-1 * (event.delta / 120)),
                "units",
            )

        self._canvas.bind_all(
            "<MouseWheel>",
            _on_mousewheel,
        )

        body.columnconfigure(0, weight=1)
        body.rowconfigure(4, weight=1, minsize=240)

        form_outer, form_card = AppTheme.build_card(
            body,
            "Connection Settings"
        )
        form_outer.grid(
            row=0,
            column=0,
            sticky="ew",
            pady=(0, AppTheme.SECTION_PADY),
        )

        pad = AppTheme.FIELD_PADY

        AppTheme.make_label(
            form_card,
            "Remote Name",
        ).grid(
            row=0,
            column=0,
            sticky="w",
            pady=(0, 6),
        )

        self.remote_entry = tk.Entry(
            form_card,
            width=48
        )
        self.remote_entry.grid(
            row=1,
            column=0,
            columnspan=2,
            sticky="ew",
            pady=(0, pad)
        )
        AppTheme.style_entry(
            self.remote_entry,
            self.fonts
        )

        AppTheme.make_label(
            form_card,
            "Folder URL / ID",
        ).grid(
            row=2,
            column=0,
            sticky="w",
            pady=(0, 6),
        )

        self.folder_entry = tk.Entry(
            form_card,
            width=48
        )
        self.folder_entry.grid(
            row=3,
            column=0,
            columnspan=2,
            sticky="ew",
            pady=(0, pad)
        )
        AppTheme.style_entry(
            self.folder_entry,
            self.fonts
        )

        AppTheme.make_label(
            form_card,
            "Drive Letter",
        ).grid(
            row=4,
            column=0,
            sticky="w",
            pady=(0, 6),
        )

        self.drive_entry = tk.Entry(
            form_card,
            width=8
        )
        self.drive_entry.grid(
            row=5,
            column=0,
            sticky="w",
            pady=(0, 4)
        )
        AppTheme.style_entry(
            self.drive_entry,
            self.fonts
        )

        form_card.columnconfigure(0, weight=1)

        stats_outer, stats_card = AppTheme.build_card(
            body,
            "Mount Status"
        )
        stats_outer.grid(
            row=1,
            column=0,
            sticky="ew",
            pady=(0, AppTheme.SECTION_PADY),
        )

        self.status_label = tk.Label(
            stats_card,
            text="Unmounted",
            bg=AppTheme.CARD,
            fg=AppTheme.TEXT_MUTED,
            font=self.fonts["stat_value"],
            anchor="w",
        )
        self.speed_label = tk.Label(
            stats_card,
            text="0 B/s",
            bg=AppTheme.CARD,
            fg=AppTheme.DRIVE_BLUE,
            font=self.fonts["stat_value"],
            anchor="w",
        )
        self.transfers_label = tk.Label(
            stats_card,
            text="0",
            bg=AppTheme.CARD,
            fg=AppTheme.DRIVE_BLUE,
            font=self.fonts["stat_value"],
            anchor="w",
        )
        self.cache_label = tk.Label(
            stats_card,
            text="0 files",
            bg=AppTheme.CARD,
            fg=AppTheme.DRIVE_BLUE,
            font=self.fonts["stat_value"],
            anchor="w",
        )

        stat_pad = (0, 6)
        AppTheme.make_label(
            stats_card,
            "State",
        ).grid(
            row=0, column=0, sticky="w", pady=stat_pad
        )
        self.status_label.grid(
            row=1, column=0, sticky="w", pady=(0, 12)
        )
        AppTheme.make_label(
            stats_card,
            "Speed",
        ).grid(
            row=0, column=1, sticky="w",
            padx=(28, 0), pady=stat_pad
        )
        self.speed_label.grid(
            row=1, column=1, sticky="w",
            padx=(28, 0), pady=(0, 12)
        )
        AppTheme.make_label(
            stats_card,
            "Transfers",
        ).grid(
            row=2, column=0, sticky="w", pady=stat_pad
        )
        self.transfers_label.grid(
            row=3, column=0, sticky="w", pady=(0, 4)
        )
        AppTheme.make_label(
            stats_card,
            "Cache",
        ).grid(
            row=2, column=1, sticky="w",
            padx=(28, 0), pady=stat_pad
        )
        self.cache_label.grid(
            row=3, column=1, sticky="w",
            padx=(28, 0), pady=(0, 4)
        )

        actions_outer, actions_card = (
            AppTheme.build_card(
                body,
                "Actions"
            )
        )
        actions_outer.grid(
            row=2,
            column=0,
            sticky="ew",
            pady=(0, AppTheme.SECTION_PADY),
        )

        button_frame = AppTheme.make_frame(
            actions_card
        )
        button_frame.pack(fill="x")

        row_one = AppTheme.make_frame(button_frame)
        row_one.pack(fill="x", pady=(0, 8))

        row_two = AppTheme.make_frame(button_frame)
        row_two.pack(fill="x")

        AppTheme.make_button(
            row_one,
            "Install Rclone",
            self.install_rclone,
        ).pack(
            side="left",
            padx=(0, 10),
        )

        AppTheme.make_button(
            row_one,
            "Install WinFsp",
            self.install_winfsp,
        ).pack(
            side="left",
            padx=(0, 10),
        )

        AppTheme.make_button(
            row_one,
            "Authenticate",
            self.authenticate,
            variant="accent",
        ).pack(
            side="left",
            padx=(0, 10),
        )

        AppTheme.make_button(
            row_two,
            "Mount",
            self.mount,
            variant="primary",
        ).pack(
            side="left",
            padx=(0, 10),
        )

        AppTheme.make_button(
            row_two,
            "Unmount",
            self.unmount,
            variant="danger",
        ).pack(
            side="left",
            padx=(0, 10),
        )

        AppTheme.make_button(
            row_two,
            "Open Folder",
            self.open_folder,
            variant="accent",
        ).pack(
            side="left",
            padx=(0, 10),
        )

        footer = tk.Frame(
            body,
            bg=AppTheme.BG,
        )
        footer.grid(
            row=3,
            column=0,
            sticky="ew",
            pady=(0, AppTheme.SECTION_PADY),
        )

        self.startup_var = tk.BooleanVar()

        ttk.Checkbutton(
            footer,
            text="Mount at Windows startup",
            variable=self.startup_var
        ).pack(side="left")

        AppTheme.make_button(
            footer,
            "Save Settings",
            self.save_settings,
            variant="accent",
        ).pack(side="right")

        log_outer, log_card = AppTheme.build_card(
            body,
            "Live Logs"
        )
        log_outer.grid(
            row=4,
            column=0,
            sticky="nsew",
        )

        log_inner = tk.Frame(
            log_card,
            bg=AppTheme.CARD,
            height=240,
        )
        log_inner.pack(fill="both", expand=True)
        log_inner.pack_propagate(True)
        log_inner.columnconfigure(0, weight=1)
        log_inner.rowconfigure(0, weight=1)

        self.log = tk.Text(
            log_inner,
            height=14,
            wrap="word",
            state="normal",
            undo=False,
        )
        AppTheme.style_log(self.log, self.fonts)
        self.log.insert(
            tk.END,
            "Waiting for log messages...\n",
        )
        self.log.configure(state="disabled")

        scrollbar = ttk.Scrollbar(
            log_inner,
            command=self.log.yview
        )
        self.log.configure(
            yscrollcommand=scrollbar.set
        )
        self.log.grid(
            row=0,
            column=0,
            sticky="nsew"
        )
        scrollbar.grid(
            row=0,
            column=1,
            sticky="ns",
            padx=(6, 0)
        )

    def write_log(self, text):

        self._log_pending.append(text)

        if (
            threading.current_thread()
            is threading.main_thread()
        ):
            self._flush_log_buffer()
        else:
            self.post_ui(self._flush_log_buffer)

    def _flush_log_buffer(self):

        if not self._log_pending:
            return

        try:
            if not self.log.winfo_exists():
                return
        except tk.TclError:
            return

        chunk = (
            "\n".join(self._log_pending)
            + "\n"
        )
        self._log_pending.clear()

        self.log.configure(state="normal")
        self.log.insert(tk.END, chunk)

        line_count = int(
            self.log.index("end-1c").split(".")[0]
        )
        if line_count > LOG_MAX_LINES:
            self.log.delete(
                "1.0",
                f"{line_count - LOG_MAX_LINES}.0"
            )

        self.log.see(tk.END)
        self.log.configure(state="disabled")

    def ensure_managers(self):

        exe = self.rclone.ensure()

        if not self.auth_manager:
            self.auth_manager = AuthManager(exe)

        if not self.remote_manager:
            self.remote_manager = RemoteManager(exe)

        if not self.mount_manager:
            self.mount_manager = MountManager(exe)

        return exe

    def normalized_drive_from(self, value):

        drive = (
            value.strip()
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

    def remote_name_from(self, value):

        name = value.strip()

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

    def _restore_mount_session_async(self):

        def task():
            session = (
                self.session_store.load_active()
            )
            if not session:
                return

            try:
                self.ensure_managers()
                self.post_ui(
                    self._attach_restored_session,
                    session
                )
            except Exception as ex:
                logger.warning(
                    "Could not restore mount "
                    "session: %s",
                    ex
                )
                self.session_store.clear()

        threading.Thread(
            target=task,
            daemon=True
        ).start()

    def _attach_restored_session(self, session):

        self.mount_manager.attach_session(session)
        self.mounting = True
        self.remote_entry.delete(0, tk.END)
        self.remote_entry.insert(
            0,
            session.remote_name
        )
        self.drive_entry.delete(0, tk.END)
        self.drive_entry.insert(
            0,
            session.drive_letter
        )
        logger.info(
            "Reconnected to active mount "
            "(pid=%s).",
            session.pid
        )
        self.start_stats_polling()

    def start_stats_polling(self):

        if self._stats_polling:
            return

        self._stats_polling = True
        self._schedule_stats_poll()

    def stop_stats_polling(self):

        self._stats_polling = False
        self._last_stats = None

        if self.stats_job:
            self.after_cancel(self.stats_job)
            self.stats_job = None

        self.status_label.configure(
            text="Unmounted",
            fg=AppTheme.TEXT_MUTED,
        )
        self.speed_label.configure(text="0 B/s")
        self.transfers_label.configure(text="0")
        self.cache_label.configure(text="0 files")

    def _schedule_stats_poll(self):

        if (
            not self._stats_polling
            or self._shutting_down
        ):
            return

        self.stats_job = self.after(
            STATS_POLL_MS,
            self._poll_stats_async
        )

    def _poll_stats_async(self):

        if (
            not self._stats_polling
            or self._shutting_down
        ):
            return

        def worker():

            if not self.mount_manager:
                self.post_ui(self._on_mount_stopped)
                return

            if not self.mount_manager.is_process_alive():
                self.post_ui(self._on_mount_stopped)
                return

            summary = (
                self.mount_manager
                .get_stats_summary()
            )
            self.post_ui(
                self._update_stats_ui,
                summary
            )

        threading.Thread(
            target=worker,
            daemon=True
        ).start()

        self._schedule_stats_poll()

    def _update_stats_ui(self, summary):

        if self._shutting_down:
            return

        snapshot = (
            summary["mounted"],
            summary["speed"],
            summary["transfers"],
            summary["cache"],
        )

        if snapshot == self._last_stats:
            return

        self._last_stats = snapshot

        self.status_label.configure(
            text=(
                "Mounted"
                if summary["mounted"]
                else "Unmounted"
            ),
            fg=(
                AppTheme.GREEN
                if summary["mounted"]
                else AppTheme.TEXT_MUTED
            ),
        )
        self.speed_label.configure(
            text=summary["speed"]
        )
        self.transfers_label.configure(
            text=str(summary["transfers"])
        )
        self.cache_label.configure(
            text=summary["cache"]
        )

    def _on_mount_stopped(self):

        if self.mounting:
            self.mounting = False
            self.session_store.clear()

        self.stop_stats_polling()

    def stream_mount_logs(self):

        if not self.mount_process:
            return

        stream = self.mount_process.stdout

        if not stream:
            return

        for line in stream:
            line = line.strip()
            if line:
                logger.debug(
                    "[rclone] %s",
                    line
                )

        exit_code = self.mount_process.poll()
        self.mounting = False
        self.post_ui(self.stop_stats_polling)

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
                existing = self.rclone.find_in_tools()
                if existing:
                    logger.info(
                        "Rclone is already installed: %s",
                        existing,
                    )
                    return

                logger.info("Installing rclone...")
                exe = self.rclone.ensure()
                logger.info("Installed: %s", exe)
            except Exception as ex:
                logger.error(
                    "Rclone install failed: %s",
                    ex
                )
                self.post_ui(
                    messagebox.showerror,
                    "Rclone Error",
                    str(ex)
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
                self.post_ui(
                    messagebox.showerror,
                    "WinFsp Error",
                    str(ex)
                )

        threading.Thread(
            target=task,
            daemon=True
        ).start()

    def authenticate(self):

        folder_input = self.folder_entry.get()
        remote_input = self.remote_entry.get()

        def task():
            try:
                self.ensure_managers()

                folder_id = (
                    DriveParser.extract_folder_id(
                        folder_input
                    )
                )
                name = self.remote_name_from(
                    remote_input
                )

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
                self.post_ui(
                    messagebox.showerror,
                    "Authentication Error",
                    str(ex)
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

        folder_input = self.folder_entry.get()
        drive_input = self.drive_entry.get()
        remote_input = self.remote_entry.get()

        def task():
            try:
                self.ensure_managers()

                if not self.winfsp.is_installed():
                    raise RuntimeError(
                        "WinFsp is not installed."
                    )

                folder_id = (
                    DriveParser.extract_folder_id(
                        folder_input
                    )
                )
                drive_letter = (
                    self.normalized_drive_from(
                        drive_input
                    )
                )
                name = self.remote_name_from(
                    remote_input
                )

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

                self.post_ui(
                    self.start_stats_polling
                )
                self.stream_mount_logs()

            except Exception as ex:
                self.mounting = False
                logger.error(
                    "Mount failed: %s",
                    ex
                )
                self.post_ui(
                    messagebox.showerror,
                    "Mount Error",
                    str(ex)
                )

        threading.Thread(
            target=task,
            daemon=True
        ).start()

    def unmount(self):

        def task():
            if not self.mount_manager:
                logger.info("Nothing to unmount.")
                return

            self.mount_manager.unmount()
            self.mounting = False
            self.mount_process = None
            self.session_store.clear()
            self.post_ui(self.stop_stats_polling)
            logger.info("Unmounted.")

        threading.Thread(
            target=task,
            daemon=True
        ).start()

    def open_folder(self):

        try:
            drive = (
                self.normalized_drive_from(
                    self.drive_entry.get()
                )
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
            "remote_name": (
                self.remote_entry.get()
            ),
            "folder_id": (
                self.folder_entry.get()
            ),
            "drive_letter": (
                self.drive_entry.get()
            ),
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

        self.remote_entry.insert(
            0,
            self.config_data.get(
                "remote_name",
                ""
            )
        )
        self.folder_entry.insert(
            0,
            self.config_data.get(
                "folder_id",
                ""
            )
        )
        self.drive_entry.insert(
            0,
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
                self.post_ui(
                    messagebox.showinfo,
                    "Update Available",
                    message
                )

                url = result.get("url")
                if url:
                    webbrowser.open(url)

        threading.Thread(
            target=task,
            daemon=True
        ).start()

    def on_close(self):

        self.shutdown()

    def shutdown(self):

        if self._shutting_down:
            return

        self._shutting_down = True
        self._shutdown_finished = False
        logger.info("Shutting down.")

        self._stats_polling = False

        if self.stats_job:
            try:
                self.after_cancel(self.stats_job)
            except Exception:
                pass
            self.stats_job = None

        self._log_pending.clear()

        def task():
            try:
                if self.mount_manager:
                    self.mount_manager.unmount()
            except Exception as ex:
                logger.warning(
                    "Unmount during shutdown "
                    "failed: %s",
                    ex
                )

            self.mounting = False
            self.mount_process = None
            self.post_ui(self._finish_shutdown)

        threading.Thread(
            target=task,
            daemon=True
        ).start()

        self.after(
            1500,
            self._finish_shutdown
        )

    def _finish_shutdown(self):

        if (
            self._shutdown_finished
            or not self._shutting_down
        ):
            return

        self._shutdown_finished = True

        try:
            self.quit()
        except Exception:
            pass

        try:
            self.destroy()
        except Exception:
            pass
