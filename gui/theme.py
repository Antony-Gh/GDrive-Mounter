import tkinter as tk
import sys
from tkinter import ttk

class AppTheme:

    BG = "#12151f"
    CARD = "#1c2130"
    CARD_BORDER = "#2a3145"
    INPUT_BG = "#252b3d"
    INPUT_BORDER = "#3d4660"
    INPUT_FOCUS = "#5b9aff"

    TEXT = "#eef1f8"
    TEXT_MUTED = "#9aa3b8"
    TEXT_DIM = "#6b7289"

    ACCENT = "#4285f4"
    GREEN = "#34c759"
    RED = "#ff5f57"
    YELLOW = "#febc2e"
    DRIVE_BLUE = "#5b9aff"

    LOG_BG = "#0f1219"
    LOG_FG = "#b8c0d4"

    FONT_FAMILY = "Segoe UI"
    FONT_MONO = "Cascadia Mono"

    FIELD_PADY = 14
    SECTION_PADY = 22

    @classmethod
    def _pick_family(cls):

        try:
            import tkinter.font as tkfont
            families = set(
                tkfont.families()
            )
            for name in (
                "Segoe UI",
                "Tahoma",
                "Arial",
                "Helvetica",
            ):
                if name in families:
                    return name
        except Exception:
            pass

        return "TkDefaultFont"

    @classmethod
    def fonts(cls):

        family = cls._pick_family()
        mono = cls._pick_mono()

        return {
            "title": (family, 24, "bold"),
            "subtitle": (family, 11),
            "section": (family, 12, "bold"),
            "label": (family, 11, "bold"),
            "entry": (family, 13),
            "button": (family, 10, "bold"),
            "button_sm": (family, 9, "bold"),
            "stat_label": (family, 10),
            "stat_value": (family, 11, "bold"),
            "log": (mono, 10),
            "badge": (family, 10, "bold"),
        }

    @classmethod
    def _pick_mono(cls):

        try:
            import tkinter.font as tkfont
            families = set(
                tkfont.families()
            )
            for name in (
                "Cascadia Mono",
                "Consolas",
                "Courier New",
            ):
                if name in families:
                    return name
        except Exception:
            pass

        return "Courier New"

    @classmethod
    def apply_root(cls, root):

        root.configure(bg=cls.BG)
        root.minsize(980, 820)
        root.geometry("1000x900")

        if sys.platform == "win32":
            try:
                root.state("zoomed")
            except tk.TclError:
                pass

        style = ttk.Style(root)

        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        fonts = cls.fonts()

        style.configure(
            ".",
            background=cls.BG,
            foreground=cls.TEXT,
            font=fonts["label"],
        )
        style.configure(
            "TFrame",
            background=cls.BG,
        )
        style.configure(
            "Card.TFrame",
            background=cls.CARD,
        )
        style.configure(
            "TLabel",
            background=cls.BG,
            foreground=cls.TEXT_MUTED,
            font=fonts["label"],
        )
        style.configure(
            "Card.TLabel",
            background=cls.CARD,
            foreground=cls.TEXT_MUTED,
            font=fonts["label"],
        )
        style.configure(
            "Title.TLabel",
            background=cls.BG,
            foreground=cls.TEXT,
            font=fonts["title"],
        )
        style.configure(
            "Subtitle.TLabel",
            background=cls.BG,
            foreground=cls.TEXT_DIM,
            font=fonts["subtitle"],
        )
        style.configure(
            "StatValue.TLabel",
            background=cls.CARD,
            foreground=cls.DRIVE_BLUE,
            font=fonts["stat_value"],
        )
        style.configure(
            "StatValueOk.TLabel",
            background=cls.CARD,
            foreground=cls.GREEN,
            font=fonts["stat_value"],
        )
        style.configure(
            "StatValueMuted.TLabel",
            background=cls.CARD,
            foreground=cls.TEXT_MUTED,
            font=fonts["stat_value"],
        )
        style.configure(
            "TLabelframe",
            background=cls.CARD,
            foreground=cls.TEXT,
            borderwidth=1,
            relief="solid",
            bordercolor=cls.CARD_BORDER,
        )
        style.configure(
            "TLabelframe.Label",
            background=cls.CARD,
            foreground=cls.TEXT,
            font=fonts["section"],
        )
        style.configure(
            "TButton",
            font=fonts["button"],
            padding=(14, 8),
            background=cls.INPUT_BG,
            foreground=cls.TEXT,
            borderwidth=0,
            focusthickness=0,
        )
        style.map(
            "TButton",
            background=[
                ("active", cls.INPUT_BORDER),
                ("pressed", cls.ACCENT),
            ],
            foreground=[
                ("disabled", cls.TEXT_DIM),
            ],
        )
        style.configure(
            "Primary.TButton",
            font=fonts["button"],
            padding=(16, 9),
            background=cls.GREEN,
            foreground="#0d1f12",
        )
        style.map(
            "Primary.TButton",
            background=[
                ("active", "#3de06f"),
                ("pressed", "#28a745"),
            ],
        )
        style.configure(
            "Danger.TButton",
            font=fonts["button"],
            padding=(16, 9),
            background=cls.RED,
            foreground="#fff8f7",
        )
        style.map(
            "Danger.TButton",
            background=[
                ("active", "#ff7b74"),
                ("pressed", "#e04b42"),
            ],
        )
        style.configure(
            "Accent.TButton",
            font=fonts["button"],
            padding=(14, 8),
            background=cls.ACCENT,
            foreground="#f5f9ff",
        )
        style.map(
            "Accent.TButton",
            background=[
                ("active", "#6aa8ff"),
                ("pressed", "#2f6fd6"),
            ],
        )
        style.configure(
            "TCheckbutton",
            background=cls.BG,
            foreground=cls.TEXT_MUTED,
            font=fonts["label"],
        )
        style.map(
            "TCheckbutton",
            background=[
                ("active", cls.BG),
            ],
        )
        style.configure(
            "Horizontal.TScrollbar",
            background=cls.INPUT_BG,
            troughcolor=cls.LOG_BG,
            borderwidth=0,
            arrowsize=14,
        )

        return fonts

    @classmethod
    def _button_colors(cls, variant):

        variants = {
            "default": (
                cls.INPUT_BORDER,
                cls.TEXT,
                cls.ACCENT,
            ),
            "accent": (
                cls.ACCENT,
                "#ffffff",
                "#6aa8ff",
            ),
            "primary": (
                cls.GREEN,
                "#0d1f12",
                "#3de06f",
            ),
            "danger": (
                cls.RED,
                "#ffffff",
                "#ff7b74",
            ),
        }
        return variants.get(
            variant,
            variants["default"],
        )

    @classmethod
    def make_button(
        cls,
        parent,
        text,
        command,
        variant="default",
    ):

        bg, fg, active = cls._button_colors(
            variant
        )

        return tk.Button(
            parent,
            text=text,
            command=command,
            font=cls.fonts()["button"],
            bg=bg,
            fg=fg,
            activebackground=active,
            activeforeground=fg,
            relief="raised",
            bd=0,
            padx=16,
            pady=10,
            cursor="hand2",
            highlightthickness=0,
        )

    @classmethod
    def make_frame(cls, parent):

        return tk.Frame(
            parent,
            bg=cls.CARD,
        )

    @classmethod
    def style_entry(cls, entry, fonts):

        entry.configure(
            font=fonts["entry"],
            bg=cls.INPUT_BG,
            fg=cls.TEXT,
            insertbackground=cls.DRIVE_BLUE,
            relief="flat",
            highlightthickness=2,
            highlightbackground=cls.INPUT_BORDER,
            highlightcolor=cls.INPUT_FOCUS,
            bd=0,
        )

    @classmethod
    def style_log(cls, text_widget, fonts):

        text_widget.configure(
            font=fonts["log"],
            bg=cls.LOG_BG,
            fg=cls.LOG_FG,
            insertbackground=cls.DRIVE_BLUE,
            relief="flat",
            highlightthickness=1,
            highlightbackground=cls.CARD_BORDER,
            highlightcolor=cls.CARD_BORDER,
            selectbackground=cls.ACCENT,
            selectforeground=cls.TEXT,
            padx=10,
            pady=8,
        )

    @classmethod
    def make_label(
        cls,
        parent,
        text,
        variant="muted",
    ):

        colors = {
            "muted": cls.TEXT_MUTED,
            "bright": cls.TEXT,
            "accent": cls.DRIVE_BLUE,
        }

        return tk.Label(
            parent,
            text=text,
            bg=cls.CARD,
            fg=colors.get(
                variant,
                cls.TEXT_MUTED,
            ),
            font=cls.fonts()["label"],
            anchor="w",
        )

    @classmethod
    def build_header(cls, parent):

        header = tk.Frame(parent, bg=cls.BG, height=160)
        header.pack_propagate(False)
        header.pack(
            fill="x",
            padx=28,
            pady=(22, 14),
        )

        stripe = tk.Frame(header, bg=cls.BG)
        stripe.pack(fill="x", pady=(0, 18))

        for color in (
            cls.ACCENT,
            cls.RED,
            cls.YELLOW,
            cls.GREEN,
        ):
            tk.Frame(
                stripe,
                bg=color,
                height=6,
            ).pack(
                side="left",
                fill="x",
                expand=True,
            )

        tk.Label(
            header,
            text="Google Drive",
            bg=cls.BG,
            fg=cls.DRIVE_BLUE,
            font=cls.fonts()["badge"],
            anchor="w",
        ).pack(anchor="w")

        tk.Label(
            header,
            text="Folder Mounter",
            bg=cls.BG,
            fg=cls.TEXT,
            font=cls.fonts()["title"],
            anchor="w",
        ).pack(anchor="w", pady=(4, 0))

        tk.Label(
            header,
            text=(
                "Mount a shared Google Drive folder "
                "as a local Windows drive"
            ),
            bg=cls.BG,
            fg=cls.TEXT_MUTED,
            font=cls.fonts()["subtitle"],
            anchor="w",
        ).pack(anchor="w", pady=(8, 0))

        return header

    @classmethod
    def build_card(cls, parent, title=None):

        outer = tk.Frame(
            parent,
            bg=cls.CARD_BORDER,
            padx=1,
            pady=1,
        )
        card = tk.Frame(
            outer,
            bg=cls.CARD,
            padx=22,
            pady=20,
        )
        card.pack(fill="both", expand=True)

        content = card

        if title:
            tk.Label(
                card,
                text=title,
                bg=cls.CARD,
                fg=cls.TEXT,
                font=cls.fonts()["section"],
                anchor="w",
            ).pack(
                anchor="w",
                fill="x",
                pady=(0, 14),
            )

            content = tk.Frame(
                card,
                bg=cls.CARD,
            )
            content.pack(
                fill="both",
                expand=True
            )

        return outer, content
