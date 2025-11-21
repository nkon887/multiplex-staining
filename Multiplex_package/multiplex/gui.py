# multiplex/gui.py
# GUI for CytoPrixm

from __future__ import annotations

import os
import re
import sys
import json
import time
import queue
import shutil
import errno
import threading
import subprocess
import webbrowser
import tkinter as tk
from tkinter import ttk, filedialog, simpledialog, messagebox
import tkinter.scrolledtext as st
from functools import partial
from typing import Any, Dict, List, Tuple, Optional
import smtplib
from email.mime.text import MIMEText

# --- logger & helpertools -------------------------------------------------
try:
    from multiplex.setup_logger import logger  # configured logger
except Exception:  # minimal fallback logger
    import logging
    logger = logging.getLogger("multiplex")
    if not logger.handlers:
        logging.basicConfig(level=logging.INFO)

try:
    import multiplex.helpertools as ht  # helpertools
except Exception:
    class _HTFallback:
        @staticmethod
        def correct_path(*parts):
            return os.path.normpath(os.path.join(*parts))
        @staticmethod
        def setting_directory(base, sub):
            p = os.path.join(base, sub)
            os.makedirs(p, exist_ok=True)
            return p
        @staticmethod
        def read_data_from_csv(path):
            import csv
            with open(path, newline="", encoding="utf-8") as f:
                return list(csv.DictReader(f))
    ht = _HTFallback()  # type: ignore


# ==============================================================================
#                                UI LOG FEEDER
# ==============================================================================
class _UILogFeeder:
    """Thread-safe queue writer that pumps text into a Tk Text widget."""
    def __init__(self, text_widget: tk.Text):
        self.text_widget = text_widget
        self.queue: "queue.Queue[str]" = queue.Queue()

    def write(self, s: str) -> None:
        if s:
            self.queue.put(s)

    def flush(self) -> None:
        pass

    def pump(self):
        try:
            while True:
                s = self.queue.get_nowait()
                self.text_widget.insert("end", s)
                self.text_widget.see("end")
        except queue.Empty:
            pass

# ==============================================================================
#                              COMMAND BUILDER
# ==============================================================================
class _CommandBuilder:
    """
    Builds shell commands for FIJI and Python steps based on the pipeline
    configuration and UI selections. Uses activate.bat for envs and %FIJIPATH%
    for Fiji
    """
    def __init__(
        self,
        packages: List[str],
        envs: List[str],
        main_work_dir: str,
        main_py: str,
        macro_py: str,
        csv_ext: str,
        metadata_file: str,
        tar_envs_dir: str,
        dapiseg_steps: List[str],
        dapiseg_subfolders: List[str],
        subfolders_list: List[str],
        align_steps: List[str],
        stitching_steps: List[str],
        merge_steps: List[str],
        bg_steps: List[str],
        cropping_exp_steps: List[str],
        fast_button_step: List[str],
    ):
        self.packages = packages
        self.envs = envs
        self.main_work_dir = main_work_dir
        self.main_py = main_py
        self.macro_py = macro_py
        self.csv_ext = csv_ext
        self.metadata_file = metadata_file
        self.tar_envs_dir = tar_envs_dir
        self.dapiseg_steps = dapiseg_steps
        self.dapiseg_subfolders = dapiseg_subfolders
        self.subfolders_list = subfolders_list
        self.align_steps = align_steps
        self.stitching_steps = stitching_steps
        self.merge_steps = merge_steps
        self.bg_steps = bg_steps
        self.cropping_exp_steps = cropping_exp_steps
        self.fast_button_step = fast_button_step

    @staticmethod
    def _q(s: str) -> str:
        # Quote when spaces/special characters present
        if any(ch in s for ch in (" ", "(", ")", "&", ";")):
            return f"\"{s}\""
        return s

    def build(
        self,
        parametersets: List[Tuple[str, str, str]],   # (package, env, step)
        command_step: str,
        inputpaths: str,
        source_dir: str,
        destination_dir: str,
        pipeline_steps: List[str],
        force_save: int,
        crop_option: str,
        gpu_selected: bool,
    ) -> List[str]:
        cmds: List[str] = []

        pipe_space = " ".join(pipeline_steps)
        stitch_space = " ".join(self.stitching_steps)
        align_space = " ".join(self.align_steps)
        dapi_space = " ".join(self.dapiseg_steps)
        merge_space = " ".join(self.merge_steps)
        bg_space = " ".join(self.bg_steps)
        crop_exp_space = " ".join(self.cropping_exp_steps)
        fast_space = " ".join(self.fast_button_step)
        subfolders_space = " ".join(self.subfolders_list)
        subfolders_comma = ",".join(self.subfolders_list)
        realign_comma = ",".join(self.dapiseg_subfolders)
        dapiseg_subfolders_space = " ".join(self.dapiseg_subfolders)

        for package, env, step in parametersets:

            # Route 1: Fiji macro (packages[0])
            if package == self.packages[0]:
                # %FIJIPATH% --ij2 --run macro.py "args"
                args = (
                    f"base_dir='{source_dir}', "
                    f"working_dir='{self.main_work_dir}', "
                    f"target_dir='{destination_dir}', "
                    f"step='{step}', "
                    f"pipeline_steps='{','.join(pipeline_steps)}', "
                    f"subfolders='{subfolders_comma}', "
                    f"realignment_subfolders='{realign_comma}', "
                    f"dapiseg_subfolders='{','.join(self.dapiseg_subfolders)}', "
                    f"crop_option='{crop_option}', "
                    f"forceSave='{force_save}'"
                )
                cmds.append(f"%FIJIPATH% --ij2 --run {self._q(self.macro_py)} \"{args}\"")
                continue

            # Route 2: Python main with environment activation (packages[1])
            if package == self.packages[1] and env:
                # Special case — DAPISEG: per-patient runs using metadata
                if step in self.dapiseg_steps:
                    folder = ht.correct_path(destination_dir, self.main_work_dir)
                    ht.setting_directory(destination_dir, self.subfolders_list[4])
                    dapi_in = ht.setting_directory(destination_dir, self.dapiseg_subfolders[0])
                    dapi_out = ht.setting_directory(destination_dir, self.dapiseg_subfolders[1])

                    # Discover patient IDs from metadata CSV
                    patient_ids: List[str] = []
                    try:
                        file_list = os.listdir(folder)
                    except Exception:
                        file_list = []

                    fnames = [
                        f for f in file_list
                        if os.path.isfile(ht.correct_path(folder, f))
                        and f.lower().endswith(self.csv_ext)
                        and f.lower() == self.metadata_file.lower()
                    ]
                    if len(fnames) == 1:
                        data = ht.read_data_from_csv(ht.correct_path(folder, self.metadata_file))
                        for row in data:
                            if "expID" in row:
                                patient_ids.append(row["expID"])
                    patient_ids = list(dict.fromkeys(patient_ids))

                    env_dir_path = ht.correct_path(self.tar_envs_dir, env)
                    root = os.path.dirname(os.path.realpath(__file__))
                    dapi_main = os.path.join(root, "dapi_seg_main.py")
                    for pid in patient_ids:
                        cmds.append(" && ".join([
                            f"cd {self._q(env_dir_path)}",
                            r".\Scripts\activate.bat",
                            f"python {self._q(dapi_main)} --input {self._q(dapi_in)} --out {self._q(dapi_out)} --patientID {self._q(pid)}",
                            r".\Scripts\deactivate.bat",
                        ]))
                else:
                    env_dir_path = ht.correct_path(self.tar_envs_dir, env)
                    cmd = [
                        f"cd {self._q(env_dir_path)}",
                        r".\Scripts\activate.bat",
                        f"{package} {self._q(self.main_py)} "
                        f"--source {self._q(source_dir)} "
                        f"--target {self._q(destination_dir)} "
                        f"--working_dir {self._q(self.main_work_dir)} "
                        f"--env {self._q(env)} "
                        f"--step {self._q(step)} "
                        f"--pipeline_steps {pipe_space} "
                        f"--stitching_steps {stitch_space} "
                        f"--dapiseg_steps {dapi_space} "
                        f"--merge_channels_steps {merge_space} "
                        f"--bg_steps {bg_space} "
                        f"--cropping_exp_steps {crop_exp_space} "
                        f"--fast_button_step {fast_space} "
                        f"--align_steps {align_space} "
                        f"--subfolders {subfolders_space} "
                        f"--dapiseg_subfolders {dapiseg_subfolders_space} "
                        f"--forceSave {force_save}",
                        r".\Scripts\deactivate.bat",
                    ]
                    cmds.append(" && ".join(cmd))
                continue

            logger.info("Unknown package/route: %s", package)

        return cmds

# ==============================================================================
#                                        APP
# ==============================================================================
class App:
    """
    creates interface of the pipeline
    """

    # ------------------------------------------------------------------
    # INIT
    # ------------------------------------------------------------------
    def __init__(
        self, master,
        pipeline_params,
        stitching_steps,
        align_steps,
        dapiseg_steps,
        merge_channels_steps,
        bg_steps,
        cropping_experimental_steps,
        fast_button_step,
        subfolders_list,
        realignment_subfolder_list,
        dapiseg_subfolder_list,
        command_arguments,
        packages,
        envs,
        main_work_dir,
        main_py_PATH,
        macro_py_PATH,
        csv_ext,
        metadata_file,
        tar_envs_dir,
    ):

        self.master = master
        try:
            # DPI scaling (Windows HiDPI)
            from ctypes import windll  # type: ignore
            windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass
        try:
            if float(self.master.tk.call('tk', 'scaling')) < 1.5:
                self.master.tk.call('tk', 'scaling', 1.5)
        except Exception:
            pass

        # Model/config (unchanged)
        self.pipeline_params = pipeline_params
        self.stitching_steps = stitching_steps
        self.align_steps = align_steps
        self.dapiseg_steps = dapiseg_steps
        self.merge_channels_steps = merge_channels_steps
        self.bg_steps = bg_steps
        self.cropping_experimental_steps = cropping_experimental_steps
        self.fast_button_step = fast_button_step
        self.subfolder_list = subfolders_list
        self.realignment_subfolder_list = realignment_subfolder_list
        self.dapiseg_subfolder_list = dapiseg_subfolder_list
        self.command_arguments = command_arguments
        self.packages = packages
        self.envs = envs
        self.main_work_dir = main_work_dir
        self.main_py_PATH = main_py_PATH
        self.macro_py_PATH = macro_py_PATH
        self.csv_ext = csv_ext
        self.metadata_file = metadata_file
        self.tar_envs_dir = tar_envs_dir

        # GUI State
        self.var_source = tk.StringVar()
        self.var_dest = tk.StringVar()
        self.var_gpu = tk.BooleanVar(value=False)
        self.var_forcesave = tk.BooleanVar(value=False)
        self.var_crop = tk.StringVar(value="manual")
        self.var_notify = tk.BooleanVar(value=False)  # off by default (email optional)

        self.current_font_size = 10

        self._build_styles()
        self._build_ui()

        # Live log feeder
        self._ui_log = _UILogFeeder(self.txt_output)
        self._pump_ui_log()

        self.txt_output.bind("<MouseWheel>", self._mouse_scroll)
        # Command builder
        self._builder = _CommandBuilder(
            packages=self.packages,
            envs=self.envs,
            main_work_dir=self.main_work_dir,
            main_py=self.main_py_PATH,
            macro_py=self.macro_py_PATH,
            csv_ext=self.csv_ext,
            metadata_file=self.metadata_file,
            tar_envs_dir=self.tar_envs_dir,
            dapiseg_steps=self.dapiseg_steps,
            dapiseg_subfolders=self.dapiseg_subfolder_list,
            subfolders_list=self.subfolder_list,
            align_steps=self.align_steps,
            stitching_steps=self.stitching_steps,
            merge_steps=self.merge_channels_steps,
            bg_steps=self.bg_steps,
            cropping_exp_steps=self.cropping_experimental_steps,
            fast_button_step=self.fast_button_step,
        )

        # Buttons map: (step, inputpaths) -> Button
        self._buttons: Dict[Tuple[str, str], ttk.Button] = {}

        # Build sidebar step buttons (from pipeline order)
        self._build_sidebar_buttons()

        # Initialize status
        self._set_status("Ready")
        self._append_log("Select Source & Destination, then start any enabled step.\n")

        # Disable until IO set
        self._refresh_step_buttons()

        # Close hook
        self.master.protocol("WM_DELETE_WINDOW", self._on_close)

    # ------------------------------------------------------------------
    # Styles
    # ------------------------------------------------------------------
    def _build_styles(self):
        s = ttk.Style(self.master)
        try:
            s.theme_use("clam")
        except Exception:
            pass

        # Global dark palette
        s.configure(".", background="#121212", fieldbackground="#1E1E1E", foreground="white")
        s.configure("TFrame", background="#121212")
        s.configure("TLabelframe", background="#121212", foreground="#4CAF50")
        s.configure("TLabelframe.Label", background="#121212", foreground="#4CAF50")
        s.configure("TLabel", background="#121212", foreground="white")
        s.configure("TEntry", fieldbackground="#1E1E1E", foreground="white")
        s.configure("TButton", padding=(14, 8))
        s.map("TButton", background=[("active", "#333333")])
        # ---------------- Sidebar buttons ----------------
        # Normal (default) step button
        s.configure(
            "Sidebar.TButton",
            background="#1E1E1E",
            foreground="white",
            font=("Helvetica", 11, "bold"),
            padding=6,
            borderwidth=0,
            relief="flat",
            focusthickness=0,
            focustcolor="",
        )
        s.map(
            "Sidebar.TButton",
            background=[("active", "#333333")],
            relief=[("pressed", "flat"), ("active", "flat")],
        )

        # Step finished successfully
        s.configure(
            "Sidebar.Done.TButton",
            background="#2E7D32",  # dark green
            foreground="white",
            font=("Helvetica", 11, "bold"),
            padding=6,
            borderwidth=0,
            relief="flat",
            focusthickness=0,
            focustcolor="",
        )
        s.map(
            "Sidebar.Done.TButton",
            background=[("active", "#388E3C")],
            relief=[("pressed", "flat"), ("active", "flat")],
        )

        # Step finished with errors
        s.configure(
            "Sidebar.Error.TButton",
            background="#C62828",  # red
            foreground="white",
            font=("Helvetica", 11, "bold"),
            padding=6,
            borderwidth=0,
            relief="flat",
            focusthickness=0,
            focustcolor="",
        )
        s.map(
            "Sidebar.Error.TButton",
            background=[("active", "#E53935")],
            relief=[("pressed", "flat"), ("active", "flat")],
        )
        s.configure("Green.Horizontal.TProgressbar",
                   troughcolor="#1E1E1E", background="#4CAF50")
        # dark vertical scrollbar
        s.layout("Dark.Vertical.TScrollbar", [
            ("Vertical.Scrollbar.trough", {
                "children": [
                    ("Vertical.Scrollbar.thumb", {"expand": True, "sticky": "nswe"})
                ],
                "sticky": "ns"
            })
        ])

        s.configure("Dark.Vertical.TScrollbar",
                    gripcount=0,
                    background="#444444",
                    darkcolor="#444444",
                    lightcolor="#444444",
                    troughcolor="#1E1E1E",
                    bordercolor="#1E1E1E",
                    arrowcolor="#4CAF50",
                    relief="flat",
                    borderwidth=0)

        s.map("Dark.Vertical.TScrollbar",
              background=[("active", "#666666"), ("pressed", "#888888")],
              troughcolor=[("active", "#1E1E1E")])

    def apply_font_size(self, new_size: int):
        """
        Dynamically adjust the font size of the output window and other text widgets.
        Bound to View → Increase / Decrease / Reset Font Size.
        """
        try:
            # Clamp between 8–20
            new_size = max(8, min(20, new_size))
            self.current_font_size = new_size

            # Update the output text widget
            if hasattr(self, "txt_output"):
                self.txt_output.configure(font=("TkFixedFont", new_size))

            # update other text widgets
            for w in getattr(self, "_open_text_windows", []):
                try:
                    w.configure(font=("TkFixedFont", new_size))
                except Exception:
                    pass

            self._set_status(f"Font size: {new_size} pt", "info")
        except Exception as e:
            logger.warning("Failed to apply font size: %s", e)

    def _mark_step_style(self, step: str, style_name: str) -> None:
        """
        Apply a ttk style to all sidebar buttons belonging to a given pipeline step.
        """
        for (s, inputpaths), btn in self._buttons.items():
            if s == step:
                btn.configure(style=style_name)

    # ------------------------------------------------------------------
    # Tooltips
    # ------------------------------------------------------------------
    def create_tooltip(self, widget, text, delay=400):
        """
        Usage: create_tooltip(widget, "text").
        """
        tip = None
        after_id = None

        def show_tip():
            nonlocal tip
            tip = tk.Toplevel(widget)
            tip.withdraw()
            tip.wm_overrideredirect(True)
            tip.configure(bg="#333333")

            label = tk.Label(
                tip, text=text, bg="#333333", fg="white",
                justify="left", relief="solid",
                borderwidth=1, padx=8, pady=6,
                font=("Helvetica", 10)
            )
            label.pack()

            x = widget.winfo_pointerx() + 16
            y = widget.winfo_pointery() + 10

            tip.update_idletasks()
            sw = widget.winfo_screenwidth()
            sh = widget.winfo_screenheight()

            # Bounds
            if x + tip.winfo_width() > sw:
                x = sw - tip.winfo_width() - 10
            if y + tip.winfo_height() > sh:
                y = sh - tip.winfo_height() - 10

            tip.geometry(f"+{x}+{y}")
            tip.deiconify()

        def schedule(event=None):
            nonlocal after_id
            after_id = widget.after(delay, show_tip)

        def hide(event=None):
            nonlocal tip, after_id
            if after_id:
                widget.after_cancel(after_id)
                after_id = None
            if tip:
                tip.destroy()
                tip = None

        widget.bind("<Enter>", schedule)
        widget.bind("<Leave>", hide)
        widget.bind("<ButtonPress>", hide)

    # ------------------------------------------------------------------
    # Mouse_Scrollbar
    # ------------------------------------------------------------------
    def _mouse_scroll(self, event):
        self.txt_output.yview_scroll(int(-1 * (event.delta / 120)), "units")
        return "break"

    # ------------------------------------------------------------------
    # Output log helpers (Clear / Save / Copy)
    # ------------------------------------------------------------------

    def clear_log(self):
        """Clear the text log in the output panel."""
        try:
            if hasattr(self, "output_text"):
                self.output_text.delete("1.0", tk.END)
            elif hasattr(self, "txt_output"):
                self.txt_output.delete("1.0", tk.END)
            self._set_status("Log cleared", "info")
        except Exception as e:
            logger.warning("Failed to clear log: %s", e)

    def save_log(self):
        """Save the current log to a text file."""
        try:
            content = ""
            if hasattr(self, "output_text"):
                content = self.output_text.get("1.0", tk.END)
            elif hasattr(self, "txt_output"):
                content = self.txt_output.get("1.0", tk.END)
            if not content.strip():
                messagebox.showinfo("Save Log", "Nothing to save — log is empty.")
                return

            file = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
            )
            if file:
                with open(file, "w", encoding="utf-8") as f:
                    f.write(content)
                self._set_status(f"Log saved to {os.path.basename(file)}", "success")
        except Exception as e:
            logger.exception("Failed to save log: %s", e)
            messagebox.showerror("Error", f"Could not save log:\n{e}")

    def copy_log(self):
        """Copy the full log text to clipboard."""
        try:
            if hasattr(self, "output_text"):
                content = self.output_text.get("1.0", tk.END)
            else:
                content = self.txt_output.get("1.0", tk.END)

            if not content.strip():
                self._set_status("Nothing to copy", "info")
                return

            self.master.clipboard_clear()
            self.master.clipboard_append(content)
            self._set_status("Log copied to clipboard", "success")

        except Exception as e:
            logger.error("Copy log failed: %s", e)
            messagebox.showerror("Error", f"Could not copy log:\n{e}")

    # ------------------------------------------------------------------
    # UI layout
    # ------------------------------------------------------------------
    def _build_ui(self):
        # Main frames
        self.frm_main = ttk.Frame(self.master)
        self.frm_main.pack(fill="both", expand=True, padx=10, pady=10)

        self.frm_left = ttk.Frame(self.frm_main, width=280)
        self.frm_left.pack(side="left", fill="y")

        # --- Logo (from file) ---
        logo_path = os.path.join(os.path.dirname(__file__), "assets", "logo.png")

        self._logo_img = None  # keep a reference to avoid garbage collection
        if os.path.exists(logo_path):
            import importlib.resources as resources
            from PIL import Image, ImageTk

            # runtime-safe loading inside _build_ui()
            try:
                with resources.files("multiplex.assets").joinpath("logo.png").open("rb") as f:
                    img = Image.open(f)
                    img = img.resize((160, 160), Image.LANCZOS)
                    self.logo_photo = ImageTk.PhotoImage(img)
                    ttk.Label(self.frm_left, image=self.logo_photo).pack(pady=(10, 10))
            except Exception as e:
                print(f"Could not load logo: {e}")
                ttk.Label(self.frm_left, text="CP", foreground="white").pack(pady=10)

        else:
            # fallback text if no logo file exists
            ttk.Label(
                self.frm_left,
                text="CYTOPRIXM",
                font=("Helvetica", 18, "bold"),
                foreground="#4CAF50"
            ).pack(pady=(10, 4))

        # ttk.Separator(self.frm_left).pack(fill="x", pady=8)

        self.frm_right = ttk.Frame(self.frm_main)
        self.frm_right.pack(side="right", fill="both", expand=True)

        ## Logo
        #lbl_logo = ttk.Label(self.frm_left, text="CYTOPRIXM", font=("Helvetica", 18, "bold"), foreground="#4CAF50")
        #lbl_logo.pack(pady=(8, 14))

        #ttk.Separator(self.frm_left).pack(fill="x", pady=(0, 8))

        # IO paths
        io = ttk.Labelframe(self.frm_right, text="INPUT / OUTPUT PATHS")
        io.pack(fill="x", padx=6, pady=6)

        ttk.Label(io, text="Source:").grid(row=0, column=0, sticky="w", padx=6, pady=6)
        self.ent_source = ttk.Entry(io, textvariable=self.var_source)
        self.ent_source.grid(row=0, column=1, sticky="ew", padx=6, pady=6)
        ttk.Button(io, text="Browse", command=self._browse_source).grid(row=0, column=2, padx=6, pady=6)
        io.columnconfigure(1, weight=1)
        self.create_tooltip(self.ent_source, "Select the folder that contains your raw input images.")

        ttk.Label(io, text="Destination:").grid(row=1, column=0, sticky="w", padx=6, pady=6)
        self.ent_dest = ttk.Entry(io, textvariable=self.var_dest)
        self.ent_dest.grid(row=1, column=1, sticky="ew", padx=6, pady=6)
        ttk.Button(io, text="Browse", command=self._browse_dest).grid(row=1, column=2, padx=6, pady=6)
        self.create_tooltip(self.ent_dest, "Select the folder where processed outputs will be written.")

        # --- Hover status bindings ---
        self.ent_source.bind("<Enter>", lambda e: self._set_status("Select source folder for raw input", "info"))
        self.ent_source.bind("<Leave>", lambda e: self._set_status("Ready", "default"))

        self.ent_dest.bind("<Enter>", lambda e: self._set_status("Select destination folder for output", "info"))
        self.ent_dest.bind("<Leave>", lambda e: self._set_status("Ready", "default"))

        # Parameters
        params = ttk.Labelframe(self.frm_right, text="STEP PARAMETERS")
        params.pack(fill="x", padx=6, pady=6)

        r = 0
        self.chk_gpu = ttk.Checkbutton(params, text="GPU", variable=self.var_gpu)
        self.chk_gpu.grid(row=r, column=0, sticky="w", padx=6, pady=4)
        self.chk_force = ttk.Checkbutton(params, text="Force Save", variable=self.var_forcesave)
        self.chk_force.grid(row=r, column=1, sticky="w", padx=6, pady=4)
        self.chk_notify = ttk.Checkbutton(params, text="Notify by Email", variable=self.var_notify)
        self.chk_notify.grid(row=r, column=2, sticky="w", padx=6, pady=4)

        r += 1
        ttk.Label(params, text="Crop mode:").grid(row=r, column=0, sticky="w", padx=6, pady=4)
        for i, (label, val) in enumerate([("Manual", "manual"), ("Semiautomatic", "semiautomatic"), ("Automatic", "automatic")]):
            ttk.Radiobutton(params, text=label, value=val, variable=self.var_crop).grid(row=r, column=i+1, sticky="w", padx=6, pady=4)
        self.create_tooltip(params, "GPU speeds DAPISEG; Force Save overwrites; choose crop mode for CROP step; Notify by Email notifies when the step is complete")

        # Output
        out = ttk.Labelframe(self.frm_right, text="OUTPUT MESSAGES")
        out.pack(fill="both", expand=True, padx=6, pady=6)

        # Frame to hold text + scrollbar
        out_frame = ttk.Frame(out)
        out_frame.pack(fill="both", expand=True, padx=6, pady=6)

        # Text area
        self.txt_output = tk.Text(
            out_frame,
            wrap="word",
            font=("TkFixedFont", 10),
            background="#121212",
            foreground="white",
            insertbackground="white",
            borderwidth=0,
            highlightthickness=0,
        )
        self.txt_output.pack(side="left", fill="both", expand=True)

        # Vertical scrollbar
        scroll = ttk.Scrollbar(
            out_frame,
            orient="vertical",
            command=self.txt_output.yview,
            style="Dark.Vertical.TScrollbar"
        )
        scroll.pack(side="right", fill="y", padx=(4, 0))

        self.txt_output.configure(yscrollcommand=scroll.set)

        # Status bar + progress
        self.frm_status = ttk.Frame(self.master)
        self.frm_status.pack(side="bottom", fill="x")
        self.var_status = tk.StringVar(value="")
        self.lbl_status = ttk.Label(self.frm_status, textvariable=self.var_status)
        self.lbl_status.pack(side="left", padx=8, pady=6)
        self.pb = ttk.Progressbar(self.frm_status, orient="horizontal", mode="indeterminate",
                                  length=300, style="Green.Horizontal.TProgressbar")
        # Pack progressbar only while running

        # Menu
        menubar = tk.Menu(self.master, tearoff=0)

        # FILE MENU
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Clear Log", accelerator="Ctrl+L", command=self.clear_log)
        file_menu.add_command(label="Copy Log", accelerator="Ctrl+C", command=self.copy_log)
        file_menu.add_command(label="Save Log", accelerator="Ctrl+S", command=self.save_log)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", accelerator="Ctrl+Q", command=self.master.quit)
        menubar.add_cascade(label="File", menu=file_menu)

        # VIEW MENU
        view_menu = tk.Menu(menubar, tearoff=0)
        view_menu.add_command(label="Increase Font Size", accelerator="Ctrl++ / Ctrl+=",
                              command=lambda: self.apply_font_size(self.current_font_size + 1))
        view_menu.add_command(label="Decrease Font Size", accelerator="Ctrl+-",
                              command=lambda: self.apply_font_size(max(8, self.current_font_size - 1)))
        view_menu.add_command(label="Reset Font Size", accelerator="Ctrl+0", command=lambda: self.apply_font_size(11))
        menubar.add_cascade(label="View", menu=view_menu)

        # HELP MENU
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="Help", accelerator="F1", command=self._open_help)
        help_menu.add_command(label="Cite As", accelerator="Ctrl+Shift+C", command=self._open_cite)
        help_menu.add_command(label="Contact Us", accelerator="Ctrl+Shift+U", command=self._open_contact)
        help_menu.add_separator()
        help_menu.add_command(label="Set Recipient Email", command=self._ask_recipient_email)
        menubar.add_cascade(label="Help", menu=help_menu)

        self.master.config(menu=menubar)
        self.master.bind("<Control-q>", lambda e: self.master.quit())
        self.master.bind("<Control-l>", lambda e: self.clear_log())
        self.master.bind("<F1>", lambda e: self._open_help())
        self.master.bind("<Control-Shift-C>", lambda e: self._open_cite())
        self.master.bind("<Control-Shift-U>", lambda e: self._open_contact())
        self.master.bind("<Control-c>", lambda e: self.copy_log())
        self.master.bind("<Control-s>", lambda e: self.save_log())
        self.master.bind("<Control-plus>", lambda e: self.apply_font_size(self.current_font_size + 1))
        self.master.bind("<Control-=>", lambda e: self.apply_font_size(self.current_font_size + 1))
        self.master.bind("<Control-minus>", lambda e: self.apply_font_size(self.current_font_size - 1))
        self.master.bind("<Control-0>", lambda e: self.apply_font_size(10))

    def _build_sidebar_buttons(self):
        """
        Build step buttons using the order of pipeline_params keys.
        pipeline_params: Dict[(step, next_steps, inputpaths, outputpaths)] -> List[rows]
        """
        all_steps = [p[0] for p in self.pipeline_params]
        last_step = all_steps[-1]
        seen = set()
        ordered = []
        for (step, _n, _i, _o) in self.pipeline_params:
            if step not in seen:
                ordered.append(step)
                seen.add(step)

        for (step, next_steps, inputpaths, outputpaths) in self.pipeline_params:
            if step not in ordered:
                ordered.append(step)

        for (step, next_steps, inputpaths, outputpaths) in self.pipeline_params:
            # ---- Add Space Before the Last Button ----
            if step == last_step:
                separator = tk.Frame(self.frm_left, bg="#444444", height=2, width=240)
                separator.pack(side=tk.TOP, pady=10)            # ---- Create the Button ----
            btn = ttk.Button(
                self.frm_left,
                text=step.replace("_", " "),
                style="Sidebar.TButton",
                command=partial(self._on_run_step, step, inputpaths)
            )
            btn.pack(fill="x", pady=6)
            self._buttons[(step, inputpaths)] = btn

            # Hover behavior: show step name in status bar
            btn.bind("<Enter>", lambda e, s=step: self._set_status(f"Run {s}", "info"))
            btn.bind("<Leave>", lambda e: self._set_status("Ready", "default"))

    # ------------------------------------------------------------------
    # IO / status / progress
    # ------------------------------------------------------------------
    def _browse_source(self):
        folder = filedialog.askdirectory()
        if folder:
            self.var_source.set(folder)
            self._refresh_step_buttons()

    def _browse_dest(self):
        folder = filedialog.askdirectory()
        if folder:
            self.var_dest.set(folder)
            self._refresh_step_buttons()

    def _set_status(self, msg: str, level: str = "default", auto_clear: bool = False, delay: int = 3000):
        """Update the status bar message and color."""
        colors = {
            "default": "#bbbbbb",
            "success": "#4CAF50",
            "info": "#FFC107",
            "error": "tomato",
        }
        self.lbl_status.configure(foreground=colors.get(level, "#bbbbbb"))
        self.var_status.set(msg)

        # Optional auto-clear
        if auto_clear:
            self.master.after(delay, lambda: self.var_status.set("Ready"))

    def _start_progress(self):
        if not self.pb.winfo_ismapped():
            self.pb.pack(side="right", padx=8)
        self.pb.start(15)

    def _stop_progress(self):
        self.pb.stop()
        if self.pb.winfo_ismapped():
            self.pb.pack_forget()

    # ------------------------------------------------------------------
    # Help / Cite / Contact / Email
    # ------------------------------------------------------------------

    def _open_help(self):
        """
        Opens README.pdf located four levels above the program's execution
        directory (sys.argv[0]).
        """
        import os
        import sys
        import webbrowser

        # Folder where python -m multiplex is executed
        exec_dir = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0]))))))

        # One directory above execution
        parent_dir = os.path.dirname(exec_dir)

        # PDF location
        pdf_path = os.path.join(parent_dir, "README.pdf")

        if not os.path.exists(pdf_path):
            messagebox.showerror(
                "Help PDF Not Found",
                f"Could not find README.pdf in:\n{parent_dir}"
            )
            return

        try:
            webbrowser.open_new(pdf_path)
            self._set_status("Opened Help PDF", "info")
        except Exception as e:
            messagebox.showerror("Error Opening PDF", f"Could not open PDF:\n{e}")

    def _open_cite(self):
        messagebox.showinfo(
            "Cite As",
            "If you use CytoPrixm:\n\n"
            "Amiridze N, Guillot A, Berger H.\n"
            "CytoPrixm: Cell processing and registration of\n"
            "immunofluorescence multiplex microscopy.\n"
            "Charité University Medicine Berlin, 2025.\n\n"
            "DOI: 10.xxxx/xxxx"
        )

    def _open_contact(self):
        # messagebox.showinfo("Contact Us", "For support or questions, please visit our project page .")
        github_url = "https://github.com/nkon887/multiplex-staining"

        win = tk.Toplevel(self.master)
        win.title("Contact Us")
        win.configure(bg="#121212")
        win.geometry("420x200")

        ttk.Label(
            win,
            text="Contact / Support",
            font=("Helvetica", 14, "bold")
        ).pack(pady=10)

        ttk.Label(
            win,
            text="Visit our GitHub page:",
            font=("Helvetica", 11)
        ).pack(pady=4)

        # clickable label
        link = tk.Label(
            win,
            text=github_url,
            fg="#4CAF50",
            cursor="hand2",
            bg="#121212",
            font=("Helvetica", 11, "underline")
        )
        link.pack(pady=4)

        # bind click
        link.bind("<Button-1>", lambda e: webbrowser.open(github_url))

        ttk.Button(win, text="Close", command=win.destroy).pack(pady=10)

    def _settings_path(self) -> str:
        return "cytoprixm_settings.json"

    def _load_mail_setting(self, key: str) -> Optional[str]:
        path = self._settings_path()
        data = {}
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                data = {}
        return data.get(key)

    def _save_mail_setting(self, key: str, val: Any) -> None:
        path = self._settings_path()
        data = {}
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                data = {}
        data[key] = val
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f)
        except Exception as e:
            logger.warning("Failed to save settings: %s", e)

    def _ask_recipient_email(self):
        recipient = self._load_mail_setting("recipient") or ""
        newval = simpledialog.askstring("Recipient Email", "Enter recipient email address:", initialvalue=recipient)
        if newval:
            self._save_mail_setting("recipient", newval)
            self._set_status("Recipient saved", "success")

    def _send_notification(self, step_name: str, had_error: bool):
        """
        Send an email notification after a pipeline step completes.
        Uses recipient stored via 'Set Recipient Email' in the Help menu.
        Requires self.var_notify to be True.
        """
        if not self.var_notify.get():
            return  # notifications disabled

        recipient = self._load_mail_setting("recipient")
        if not recipient:
            logger.info("Notification skipped: no recipient set.")
            return

        # --- Prepare message ---
        subject = f"[CytoPrixm] Step {step_name} {'FAILED' if had_error else 'Completed'}"
        body = (
            f"Dear user,\n\n"
            f"The pipeline step '{step_name}' has {'FAILED' if had_error else 'completed successfully'}.\n\n"
            f"Source: {self.var_source.get()}\n"
            f"Destination: {self.var_dest.get()}\n\n"
            f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            f"CytoPrixm automated notification.\n"
        )
        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = subject
        msg["From"] = "cytoprixm@localhost"
        msg["To"] = recipient

        SENDER_EMAIL = os.getenv("CYTOPRIXM_EMAIL")
        SENDER_PASSWORD = os.getenv("CYTOPRIXM_PASS")

        if not SENDER_EMAIL or not SENDER_PASSWORD:
            logger.warning("Email credentials not found in environment variables.")

        try:
            # --- SMTP Setup ---
            with smtplib.SMTP("smtp.gmail.com", 587) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(SENDER_EMAIL, SENDER_PASSWORD)
                server.sendmail(msg["From"], [recipient], msg.as_string())
            self._set_status(f"Notification sent to {recipient}", "success")
            logger.info("Notification email sent to %s", recipient)
        except Exception as e:
            self._set_status("Notification failed", "error")
            logger.warning("Could not send notification: %s", e)

    # ------------------------------------------------------------------
    # Logging & pump
    # ------------------------------------------------------------------
    def _append_log(self, s: str):
        self.txt_output.insert("end", s)
        self.txt_output.see("end")

    def _pump_ui_log(self):
        self._ui_log.pump()
        self.master.after(50, self._pump_ui_log)

    # ------------------------------------------------------------------
    # Step orchestration
    # ------------------------------------------------------------------
    def _on_run_step(self, step: str, inputpaths: str):
        if step == "CLEAN_OUTPUT":
            if not messagebox.askyesno("Confirmation", "Clean intermediate data and keep only final results?"):
                self._append_log("\nThe user canceled the step execution. Doing nothing.\nDONE\n")
                return
        params = self._make_parametersets_for_step(step, inputpaths)
        self._run_step_async(step, inputpaths, params)

    def _make_parametersets_for_step(self, step: str, inputpaths: str) -> List[Tuple[str, str, str]]:
        """
        Returns [(package, env, step), ...] for the selected pipeline step.
        Handles the CROP case based on selected crop-mode. Follows
        pipeline_params layout: Dict[(step, next, input, output)] -> List[rowsets]
        """
        params: List[Tuple[str, str, str]] = []
        # Find the key for this step & inputpaths
        matches = [(s, n, i, o) for (s, n, i, o) in self.pipeline_params if s == step and i == inputpaths]
        if not matches:
            matches = [(s, n, i, o) for (s, n, i, o) in self.pipeline_params if s == step]
        if not matches:
            return params

        key = matches[0]
        block = self.pipeline_params[key]

        # CROP: choose rowset based on crop mode
        if step == "CROP":
            mapping = {"manual": 0, "semiautomatic": 1, "automatic": 2}
            idx = mapping.get(self.var_crop.get(), 0)
            if idx >= len(block):
                idx = 0
            rowset = block[idx]
            for i in range(len(rowset)):
                pkg = rowset[i][self.command_arguments[0]]
                env = rowset[i][self.command_arguments[1]]
                stp = rowset[i][self.command_arguments[2]]
                params.append((pkg, env, stp))
        else:
            for i in range(len(block)):
                pkg = block[i][self.command_arguments[0]]
                env = block[i][self.command_arguments[1]]
                stp = block[i][self.command_arguments[2]]
                params.append((pkg, env, stp))

        return params

    def _run_step_async(self, step: str, inputpaths: str, parametersets: List[Tuple[str, str, str]]):
        source = self.var_source.get().strip()
        dest = self.var_dest.get().strip()
        if not source or not dest:
            messagebox.showwarning("Missing Paths", "Please select Source and Destination folders first.")
            return

        self._append_log(f"\n[INFO] Starting {step}...\n")
        self._set_status(f"Running {step}", "info")
        self._start_progress()
        self._disable_all_buttons()

        # Build commands
        pipe_steps = [k[0] for k in self.pipeline_params.keys()]
        cmds = self._builder.build(
            parametersets=parametersets,
            command_step=step,
            inputpaths=inputpaths,
            source_dir=source,
            destination_dir=dest,
            pipeline_steps=pipe_steps,
            force_save=int(self.var_forcesave.get()),
            crop_option=self.var_crop.get(),
            gpu_selected=bool(self.var_gpu.get()),
        )

        done: List[Tuple[str, bool]] = []

        def worker():
            try:
                res = self._execute_commands(cmds)
            except Exception as e:
                logger.exception("Step failed: %s", e)
                res = (f"[ERROR] Exception: {e}\n", True)
            done.append(res)

        t = threading.Thread(target=worker, daemon=True)
        t.start()

        def poll():
            if t.is_alive():
                self.master.after(50, poll)
                return

            # finished
            self._stop_progress()
            summary, had_error = done[0]

            self._append_log(summary + "\n")
            self._append_log(f"[INFO] {step} completed.\n")

            # determine status / style
            error_detected = had_error or ("ERROR" in summary)

            if error_detected:
                # red button, error status
                self._mark_step_style(step, "Sidebar.Error.TButton")
                self._set_status(f"{step} completed with errors", "error")
            else:
                # green button, success status
                self._mark_step_style(step, "Sidebar.Done.TButton")
                self._set_status(f"{step} completed", "success")

            # enable next steps based on outputs
            self._enable_next_steps(step, summary, error_detected)

        self.master.after(50, poll)

    def _execute_commands(self, commands: List[str]) -> Tuple[str, bool]:
        """
        Executes commands sequentially, streams stdout/stderr to UI, and collects
        WARNING/ERROR lines into a summary. Returns (summary, had_error).
        """
        summary_lines: List[str] = []
        had_error = False
        split_words = ("WARNING", "ERROR")

        for cmd in commands:
            # self._ui_log.write(f"[CMD] {cmd}\n")
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
            while True:
                line = p.stdout.readline()
                if not line:
                    break
                try:
                    text = line.decode("utf-8", errors="replace")
                except Exception:
                    text = str(line)
                self._ui_log.write(text)
                if any(w in text for w in split_words):
                    summary_lines.append(text)
                    if "ERROR" in text:
                        had_error = True
            p.wait()
            rc = p.returncode
            if rc != 0:
                had_error = True
                summary_lines.append(f"[ERROR] Command exited with code {rc}\n")

        summary = "".join(summary_lines) if summary_lines else "[INFO] No warnings or errors reported.\n"
        return summary, had_error

    # ------------------------------------------------------------------
    # Enabling next steps & refresh logic
    # ------------------------------------------------------------------
    def _enable_next_steps(self, finished_step: str, result_text: str, had_error: bool):
        dest = self.var_dest.get().strip()
        err = had_error or ("ERROR" in result_text)

        transitions = [(s, n, i, o) for (s, n, i, o) in self.pipeline_params if s == finished_step]
        if not transitions:
            self._refresh_step_buttons()
            return

        _s, next_steps_str, _i, outpaths_str = transitions[0]
        next_steps = [x for x in next_steps_str.split(",") if x]
        outpaths = [ht.correct_path(dest, p) for p in outpaths_str.split(",") if p]

        for (step, inputpaths), btn in self._buttons.items():
            if step in next_steps:
                exists = all(os.path.exists(p) for p in outpaths)
                btn.configure(state=tk.NORMAL if (exists and not err) else tk.DISABLED)

        # Re-enable unrelated steps if their inputs exist
        self._refresh_step_buttons()

    def _refresh_step_buttons(self):
        src = self.var_source.get().strip()
        dst = self.var_dest.get().strip()
        have_io = bool(src and dst)

        for (step, inputpaths), btn in self._buttons.items():
            if not have_io:
                btn.configure(state=tk.DISABLED)
                continue
            # enable if inputs exist (or none required)
            needed = [ht.correct_path(dst, p.strip()) for p in inputpaths.split(",") if p.strip()]
            if not needed:
                btn.configure(state=tk.NORMAL)
            else:
                exists = all(os.path.exists(p) for p in needed)
                btn.configure(state=tk.NORMAL if exists else tk.DISABLED)

    def _disable_all_buttons(self):
        for btn in self._buttons.values():
            btn.configure(state=tk.DISABLED)

    # ------------------------------------------------------------------
    # Close
    # ------------------------------------------------------------------
    def _on_close(self):
        try:
            self.master.destroy()
        except Exception:
            os._exit(0)
