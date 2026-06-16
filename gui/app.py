import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkinter import scrolledtext
import threading
import subprocess
import os

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

        self.create_ui()

        self.load_settings()

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

    def write_log(
        self,
        text
    ):

        self.log.insert(
            tk.END,
            text + "\n"
        )

        self.log.see(
            tk.END
        )

    def install_rclone(self):

        def task():

            self.write_log(
                "Installing rclone..."
            )

            exe = (
                self.rclone.ensure()
            )

            self.write_log(
                f"Installed: {exe}"
            )

        threading.Thread(
            target=task,
            daemon=True
        ).start()

    def install_winfsp(self):

        def task():

            self.write_log(
                "Installing WinFsp..."
            )

            self.winfsp.install()

            self.write_log(
                "WinFsp installer launched."
            )

        threading.Thread(
            target=task,
            daemon=True
        ).start()

    def authenticate(self):

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

    def mount(self):

        try:

            folder_id = (
                DriveParser.extract_folder_id(
                    self.folder_var.get()
                )
            )

            exe = (
                self.rclone.ensure()
            )

            self.mount_manager = (
                MountManager(exe)
            )

            self.mount_manager.mount(
                folder_id,
                self.drive_var.get()
            )

            self.write_log(
                "Mounted successfully."
            )

        except Exception as ex:

            messagebox.showerror(
                "Error",
                str(ex)
            )

    def unmount(self):

        if self.mount_manager:

            self.mount_manager.unmount()

            self.write_log(
                "Unmounted."
            )

    def open_folder(self):

        drive = (
            self.drive_var.get()
            + ":\\"
        )

        os.startfile(
            drive
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