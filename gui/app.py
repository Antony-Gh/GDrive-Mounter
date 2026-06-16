import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkinter import scrolledtext
import threading
import subprocess
import os
import sys
from pathlib import Path

from config import ConfigManager

from core.drive_parser import DriveParser
from core.rclone_manager import RcloneManager
from core.winfsp_manager import WinFspManager
from core.mount_manager import MountManager
from core.startup_manager import StartupManager


class App(tk.Tk):

    def __init__(self):

        super().__init__()

        self.title(
            "Google Drive Folder Mounter"
        )

        self.geometry(
            "900x700"
        )

        self.config_data = (
            ConfigManager.load()
        )

        self.rclone = (
            RcloneManager()
        )

        self.winfsp = (
            WinFspManager()
        )

        self.mount_manager = None
        self.mount_process = None
        self.mounting = False
        self.startup_batch_file = (
            Path(__file__).resolve().parent.parent /
            "mount_on_startup.bat"
        )

        self.create_ui()

        self.load_settings()
        self.apply_theme()

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

        self.remote_var = (
            tk.StringVar()
        )

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

        self.folder_var = (
            tk.StringVar()
        )

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

        self.drive_var = (
            tk.StringVar()
        )

        ttk.Entry(
            main,
            textvariable=self.drive_var,
            width=10
        ).grid(
            row=2,
            column=1,
            sticky="w"
        )

        button_frame = ttk.Frame(
            main
        )

        button_frame.grid(
            row=3,
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

        self.startup_var = (
            tk.BooleanVar()
        )

        ttk.Checkbutton(
            main,
            text="Mount at startup",
            variable=self.startup_var
        ).grid(
            row=4,
            column=0,
            sticky="w"
        )

        ttk.Button(
            main,
            text="Save Settings",
            command=self.save_settings
        ).grid(
            row=4,
            column=1,
            sticky="e"
        )

        self.log = (
            scrolledtext.ScrolledText(
                main,
                height=25
            )
        )

        self.log.grid(
            row=5,
            column=0,
            columnspan=2,
            sticky="nsew"
        )

        main.columnconfigure(
            1,
            weight=1
        )

        main.rowconfigure(
            5,
            weight=1
        )

    def apply_theme(self):

        try:
            import sv_ttk
            sv_ttk.set_theme("dark")
            self.write_log(
                "Dark theme enabled."
            )
        except Exception:
            self.write_log(
                "Default theme in use."
            )

    def write_log(
        self,
        text
    ):

        def append():
            self.log.insert(
                tk.END,
                text + "\n"
            )

            self.log.see(
                tk.END
            )

        self.after(
            0,
            append
        )

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
                "Drive letter must be a single letter (A-Z)."
            )

        return drive

    def create_startup_batch(self):

        if getattr(
            sys,
            "frozen",
            False
        ):
            launcher = (
                f'"{Path(sys.executable)}"'
            )
        else:
            launcher = (
                f'"{sys.executable}" "{Path(__file__).resolve().parent.parent / "main.py"}"'
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
            self.write_log(
                "Startup enabled."
            )
        else:
            StartupManager.remove_batch(
                str(self.startup_batch_file)
            )
            self.write_log(
                "Startup disabled."
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
                self.write_log(
                    f"[rclone] {line}"
                )

        exit_code = self.mount_process.poll()
        self.mounting = False

        if exit_code is None:
            self.write_log(
                "Mount process finished."
            )
        elif exit_code == 0:
            self.write_log(
                "Mount process exited cleanly."
            )
        else:
            self.write_log(
                f"Mount process exited with code {exit_code}."
            )

    def install_rclone(self):

        def task():
            try:
                self.write_log(
                    "Installing rclone..."
                )

                exe = (
                    self.rclone.ensure()
                )

                self.write_log(
                    f"Installed: {exe}"
                )
            except Exception as ex:
                self.write_log(
                    f"Rclone install failed: {ex}"
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
                self.write_log(
                    "Installing WinFsp..."
                )

                self.winfsp.install()

                self.write_log(
                    "WinFsp installer launched."
                )
            except Exception as ex:
                self.write_log(
                    f"WinFsp install failed: {ex}"
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
                exe = self.rclone.ensure()

                subprocess.Popen(
                    [
                        exe,
                        "config"
                    ]
                )

                self.write_log(
                    "Rclone configuration opened."
                )
            except Exception as ex:
                self.write_log(
                    f"Authentication launch failed: {ex}"
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
            self.write_log(
                "Mount is already running."
            )
            return

        def task():
            try:
                folder_id = (
                    DriveParser.extract_folder_id(
                        self.folder_var.get()
                    )
                )

                drive_letter = (
                    self.normalized_drive()
                )

                exe = (
                    self.rclone.ensure()
                )

                self.mount_manager = (
                    MountManager(exe)
                )

                self.mount_process = (
                    self.mount_manager.mount(
                        folder_id,
                        drive_letter
                    )
                )
                self.mounting = True

                self.write_log(
                    f"Mount started on {drive_letter}:"
                )

                self.stream_mount_logs()

            except Exception as ex:
                self.mounting = False
                self.write_log(
                    f"Mount failed: {ex}"
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

        if self.mount_manager:

            self.mount_manager.unmount()
            self.mounting = False
            self.mount_process = None

            self.write_log(
                "Unmounted."
            )
        else:
            self.write_log(
                "Nothing to unmount."
            )

    def open_folder(self):
        try:
            drive = (
                self.normalized_drive()
                + ":\\"
            )

            if not os.path.exists(
                drive
            ):
                raise FileNotFoundError(
                    f"{drive} is not available."
                )

            os.startfile(
                drive
            )
        except Exception as ex:
            self.write_log(
                f"Open folder failed: {ex}"
            )
            messagebox.showerror(
                "Open Folder Error",
                str(ex)
            )

    def save_settings(self):

        data = {

            "remote_name":
                self.remote_var.get(),

            "folder_id":
                self.folder_var.get(),

            "drive_letter":
                self.drive_var.get(),

            "mount_on_startup":
                self.startup_var.get()
        }

        ConfigManager.save(
            data
        )

        try:
            self.apply_startup_setting()
        except Exception as ex:
            self.write_log(
                f"Startup update failed: {ex}"
            )
            messagebox.showerror(
                "Startup Error",
                str(ex)
            )
            return

        self.write_log(
            "Settings saved."
        )

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