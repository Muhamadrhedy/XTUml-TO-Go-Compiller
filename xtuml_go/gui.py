"""Polished Tkinter GUI for the xtUML to Go compiler.

Theme: Deep Navy #0C2C55, Teal #296374, Soft Cyan #629FAF, Warm Ivory #EDEEDC.
"""
import os
import tkinter as tk
from tkinter import ttk, filedialog
from .compiler import compile_source, CompileError

# Color Hunt palette
NAVY = "#0C2C55"
TEAL = "#296374"
CYAN = "#629FAF"
IVORY = "#EDEEDC"
WHITE = "#FFFFFF"
INK = "#17283D"
MUTED = "#607487"
BORDER = "#D5DFDF"
EDITOR = "#101B2B"
EDITOR_FG = "#E7EEF5"
SUCCESS = "#296374"
ERROR = "#9E3D42"
WARNING = "#8A6B2E"

SAMPLE = r"""@startuml
class Student {
    +name: String
    +nim: String
    -age: Integer
    +IsAdult(): Boolean
    +ChangeName(newName: String): String
}

class Order {
    +id: String
    +total: Float
}

state_machine OrderLifecycle for Order {
    initial Pending
    state Pending
    state Paid
    state Cancelled
    transition Pending on Pay -> Paid action MarkPaid
    transition Pending on Cancel -> Cancelled
}
@enduml
"""


class AppDialog(tk.Toplevel):
    """A themed modal dialog used instead of native messagebox popups."""
    def __init__(self, parent, title, message, kind="info", detail=None):
        super().__init__(parent)
        self.parent = parent
        self.kind = kind
        self.title(title)
        self.resizable(False, False)
        self.transient(parent)
        self.configure(bg=IVORY)
        self.result = False

        accent = {"success": TEAL, "error": ERROR, "warning": WARNING, "info": NAVY}.get(kind, NAVY)
        symbol = {"success": "✓", "error": "!", "warning": "!", "info": "i"}.get(kind, "i")

        outer = tk.Frame(self, bg=IVORY, padx=0, pady=0)
        outer.pack(fill="both", expand=True)
        top = tk.Frame(outer, bg=accent, height=8)
        top.pack(fill="x")
        top.pack_propagate(False)

        body = tk.Frame(outer, bg=IVORY, padx=24, pady=20)
        body.pack(fill="both", expand=True)
        headline = tk.Frame(body, bg=IVORY)
        headline.pack(fill="x")
        icon = tk.Label(headline, text=symbol, bg=accent, fg=WHITE,
                        font=("Segoe UI", 17, "bold"), width=2, height=1,
                        padx=3, pady=3)
        icon.pack(side="left", anchor="n", padx=(0, 12))
        title_label = tk.Label(headline, text=title, bg=IVORY, fg=NAVY,
                               font=("Segoe UI", 13, "bold"), anchor="w")
        title_label.pack(side="left", fill="x", expand=True, pady=(4, 0))
        msg = tk.Label(body, text=message, bg=IVORY, fg=INK,
                       font=("Segoe UI", 10), justify="left", anchor="w",
                       wraplength=440)
        msg.pack(fill="x", pady=(16, 8))

        if detail:
            detail_box = tk.Frame(body, bg="#F7F7EC", highlightbackground=BORDER,
                                  highlightthickness=1, padx=10, pady=8)
            detail_box.pack(fill="x", pady=(2, 8))
            tk.Label(detail_box, text=detail, bg="#F7F7EC", fg=ERROR if kind == "error" else MUTED,
                     font=("Consolas", 9), justify="left", anchor="w",
                     wraplength=430).pack(fill="x")

        actions = tk.Frame(body, bg=IVORY)
        actions.pack(fill="x", pady=(14, 0))
        button = tk.Button(actions, text="Mengerti", command=self._close,
                           bg=accent, fg=WHITE, activebackground=TEAL,
                           activeforeground=WHITE, relief="flat", bd=0,
                           font=("Segoe UI", 10, "bold"), padx=20, pady=8,
                           cursor="hand2")
        button.pack(side="right")
        self.bind("<Return>", lambda _event: self._close())
        self.bind("<Escape>", lambda _event: self._close())
        self.protocol("WM_DELETE_WINDOW", self._close)
        self.update_idletasks()
        width = max(390, self.winfo_reqwidth())
        height = self.winfo_reqheight()
        px = parent.winfo_rootx() + max(0, (parent.winfo_width() - width) // 2)
        py = parent.winfo_rooty() + max(0, (parent.winfo_height() - height) // 2)
        self.geometry(f"{width}x{height}+{px}+{py}")
        self.grab_set()
        self.focus_force()

    def _close(self):
        self.result = True
        self.destroy()


class CompilerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("xtUML → Go Compiler")
        self.geometry("1380x850")
        self.minsize(1040, 680)
        self.configure(bg=IVORY)
        self._configure_styles()
        self._build()
        self.source.insert("1.0", SAMPLE)
        self._set_log("Ready. Load a model or edit the example, then select Compile.", "info")

    def _configure_styles(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("TFrame", background=IVORY)
        style.configure("Panel.TFrame", background=WHITE)
        style.configure("TLabel", background=IVORY, foreground=INK, font=("Segoe UI", 10))
        style.configure("Muted.TLabel", background=IVORY, foreground=MUTED, font=("Segoe UI", 9))
        style.configure("PanelTitle.TLabel", background=WHITE, foreground=NAVY,
                        font=("Segoe UI", 10, "bold"))
        style.configure("TEntry", padding=(8, 6), fieldbackground=WHITE,
                        foreground=INK, font=("Segoe UI", 10))
        style.configure("TButton", padding=(12, 8), font=("Segoe UI", 10),
                        background=WHITE, foreground=NAVY, bordercolor=BORDER)
        style.map("TButton", background=[("active", "#DCE8E8"), ("pressed", "#C8DCDD")],
                  foreground=[("disabled", "#9AA8B2")])
        style.configure("Primary.TButton", padding=(14, 8), font=("Segoe UI", 10, "bold"),
                        background=TEAL, foreground=WHITE, bordercolor=TEAL)
        style.map("Primary.TButton", background=[("active", NAVY), ("pressed", NAVY)],
                  foreground=[("active", WHITE), ("pressed", WHITE)])
        style.configure("TSeparator", background=BORDER)

    def _build(self):
        # Brand header
        header = tk.Frame(self, bg=NAVY, padx=24, pady=18)
        header.pack(fill="x")
        title_row = tk.Frame(header, bg=NAVY)
        title_row.pack(fill="x")
        tk.Label(title_row, text="xtUML", bg=NAVY, fg=WHITE,
                 font=("Segoe UI", 22, "bold")).pack(side="left")
        tk.Label(title_row, text="  →  Go Compiler", bg=NAVY, fg="#B9D8E0",
                 font=("Segoe UI", 22, "bold")).pack(side="left")
        tk.Label(header, text="MODEL PARSER   •   SEMANTIC ANALYSIS   •   GO CODE GENERATION",
                 bg=NAVY, fg="#D1E1E8", font=("Segoe UI", 9)).pack(anchor="w", pady=(5, 0))

        toolbar = tk.Frame(self, bg=IVORY, padx=20, pady=12)
        toolbar.pack(fill="x")
        ttk.Button(toolbar, text="Open UML", command=self.open_file).pack(side="left", padx=(0, 7))
        ttk.Button(toolbar, text="Load example", command=self.load_example).pack(side="left", padx=7)
        ttk.Button(toolbar, text="Compile  ▶", style="Primary.TButton",
                   command=self.compile).pack(side="left", padx=7)
        ttk.Button(toolbar, text="Save Go", command=self.save_go).pack(side="left", padx=7)
        tk.Frame(toolbar, bg=BORDER, width=1, height=30).pack(side="left", padx=13)
        ttk.Label(toolbar, text="Package").pack(side="left", padx=(0, 7))
        self.package = tk.StringVar(value="main")
        ttk.Entry(toolbar, textvariable=self.package, width=13).pack(side="left")
        tk.Label(toolbar, text="  •  Save your generated code as a .go file",
                 bg=IVORY, fg=MUTED, font=("Segoe UI", 9)).pack(side="left", padx=12)

        # Editor/output panels
        panes_wrap = tk.Frame(self, bg=IVORY, padx=20, pady=0)
        panes_wrap.pack(fill="both", expand=True, pady=(0, 12))
        panes = ttk.Panedwindow(panes_wrap, orient="horizontal")
        panes.pack(fill="both", expand=True)
        left = tk.Frame(panes, bg=WHITE, highlightbackground=BORDER, highlightthickness=1)
        right = tk.Frame(panes, bg=WHITE, highlightbackground=BORDER, highlightthickness=1)
        panes.add(left, weight=1)
        panes.add(right, weight=1)
        self._make_panel_header(left, "01", "UML / xtUML SOURCE", "Edit model input")
        self._make_panel_header(right, "02", "GENERATED GO", "Read-only output")

        editor_area = tk.Frame(left, bg=EDITOR)
        editor_area.pack(fill="both", expand=True, padx=1, pady=(0, 1))
        self.source = tk.Text(editor_area, wrap="none", undo=True, font=("Consolas", 11),
                              bg=EDITOR, fg=EDITOR_FG, insertbackground=WHITE,
                              selectbackground=TEAL, selectforeground=WHITE,
                              padx=16, pady=14, relief="flat", bd=0,
                              tabs=(28,), spacing1=1, spacing3=1)
        src_y = ttk.Scrollbar(editor_area, orient="vertical", command=self.source.yview)
        src_x = ttk.Scrollbar(editor_area, orient="horizontal", command=self.source.xview)
        self.source.configure(yscrollcommand=src_y.set, xscrollcommand=src_x.set)
        self.source.grid(row=0, column=0, sticky="nsew")
        src_y.grid(row=0, column=1, sticky="ns")
        src_x.grid(row=1, column=0, sticky="ew")
        editor_area.rowconfigure(0, weight=1); editor_area.columnconfigure(0, weight=1)

        output_area = tk.Frame(right, bg=WHITE)
        output_area.pack(fill="both", expand=True, padx=1, pady=(0, 1))
        self.output = tk.Text(output_area, wrap="none", font=("Consolas", 11),
                              bg=WHITE, fg=INK, insertbackground=NAVY,
                              selectbackground=CYAN, selectforeground=WHITE,
                              padx=16, pady=14, relief="flat", bd=0,
                              state="disabled", spacing1=1, spacing3=1)
        out_y = ttk.Scrollbar(output_area, orient="vertical", command=self.output.yview)
        out_x = ttk.Scrollbar(output_area, orient="horizontal", command=self.output.xview)
        self.output.configure(yscrollcommand=out_y.set, xscrollcommand=out_x.set)
        self.output.grid(row=0, column=0, sticky="nsew")
        out_y.grid(row=0, column=1, sticky="ns")
        out_x.grid(row=1, column=0, sticky="ew")
        output_area.rowconfigure(0, weight=1); output_area.columnconfigure(0, weight=1)

        # Status and log area
        bottom = tk.Frame(self, bg=IVORY, padx=20, pady=0)
        bottom.pack(fill="x", pady=(0, 16))
        status_card = tk.Frame(bottom, bg="#F7F7EC", highlightbackground=BORDER, highlightthickness=1)
        status_card.pack(fill="x")
        status_top = tk.Frame(status_card, bg="#F7F7EC", padx=12, pady=8)
        status_top.pack(fill="x")
        self.status_dot = tk.Label(status_top, text="●", bg="#F7F7EC", fg=CYAN,
                                   font=("Segoe UI", 10, "bold"))
        self.status_dot.pack(side="left", padx=(0, 7))
        self.status = tk.StringVar(value="Ready — load a model and click Compile.")
        tk.Label(status_top, textvariable=self.status, bg="#F7F7EC", fg=INK,
                 font=("Segoe UI", 9, "bold"), anchor="w").pack(side="left", fill="x", expand=True)
        self.log = tk.Text(status_card, height=3, font=("Consolas", 9), bg="#E4EBE8",
                           fg=INK, relief="flat", padx=12, pady=8, wrap="word", bd=0)
        self.log.pack(fill="x", padx=1, pady=(0, 1))
        self.log.configure(state="disabled")

    def _make_panel_header(self, parent, number, title, subtitle):
        bar = tk.Frame(parent, bg=WHITE, padx=14, pady=11)
        bar.pack(fill="x")
        badge = tk.Label(bar, text=number, bg=TEAL, fg=WHITE,
                         font=("Segoe UI", 9, "bold"), padx=7, pady=3)
        badge.pack(side="left", padx=(0, 10))
        text_frame = tk.Frame(bar, bg=WHITE)
        text_frame.pack(side="left", fill="x", expand=True)
        tk.Label(text_frame, text=title, bg=WHITE, fg=NAVY,
                 font=("Segoe UI", 10, "bold")).pack(anchor="w")
        tk.Label(text_frame, text=subtitle, bg=WHITE, fg=MUTED,
                 font=("Segoe UI", 8)).pack(anchor="w", pady=(1, 0))
        tk.Frame(parent, bg=BORDER, height=1).pack(fill="x")

    def _set_log(self, text, kind="info"):
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.insert("1.0", text or "No warnings.")
        self.log.configure(state="disabled")
        color = {"success": SUCCESS, "error": ERROR, "warning": WARNING, "info": CYAN}.get(kind, CYAN)
        self.status_dot.configure(fg=color)

    def _dialog(self, title, message, kind="info", detail=None):
        AppDialog(self, title, message, kind=kind, detail=detail)

    def open_file(self):
        path = filedialog.askopenfilename(
            parent=self,
            title="Open UML / xtUML model",
            filetypes=[("UML / text", "*.puml *.plantuml *.xtuml *.txt"), ("All files", "*.*")]
        )
        if not path:
            return
        try:
            with open(path, encoding="utf-8") as f:
                content = f.read()
            self.source.delete("1.0", "end")
            self.source.insert("1.0", content)
            self.status.set(f"Model loaded: {os.path.basename(path)}")
            self._set_log(f"Loaded source file: {path}", "success")
        except (OSError, UnicodeError) as exc:
            self.status.set("Unable to open source file.")
            self._set_log(f"OPEN ERROR\n{exc}", "error")
            self._dialog("Could not open file", "The selected file could not be opened.", "error", str(exc))

    def load_example(self):
        self.source.delete("1.0", "end")
        self.source.insert("1.0", SAMPLE)
        self.status.set("Example model loaded. Ready to compile.")
        self._set_log("Example model loaded into the source editor.", "success")

    def compile(self):
        package_name = self.package.get().strip() or "main"
        try:
            result = compile_source(self.source.get("1.0", "end-1c"), package_name)
        except CompileError as exc:
            error_text = str(exc)
            self.status.set("Compilation failed — review the source model.")
            self._set_log("COMPILER ERROR\n" + error_text, "error")
            self._dialog("Compilation failed", "The model could not be compiled. Check the syntax and try again.",
                         "error", error_text)
            return
        except Exception as exc:  # Keep unexpected failures visible and user-friendly.
            self.status.set("Compilation stopped unexpectedly.")
            self._set_log("UNEXPECTED ERROR\n" + str(exc), "error")
            self._dialog("Unexpected compiler error", "An unexpected error occurred during compilation.",
                         "error", str(exc))
            return

        self.output.configure(state="normal")
        self.output.delete("1.0", "end")
        self.output.insert("1.0", result.output)
        self.output.configure(state="disabled")
        logs = [f"SUCCESS — {result.class_count} class(es) translated."]
        if result.warnings:
            logs.extend(["", "WARNINGS:"] + ["• " + warning for warning in result.warnings])
        self._set_log("\n".join(logs), "warning" if result.warnings else "success")
        self.status.set(f"Compilation successful — {result.class_count} class(es) translated.")
        self._dialog("Compilation successful", f"The model was translated into Go.\n\nClasses generated: {result.class_count}",
                     "warning" if result.warnings else "success",
                     "Warnings were reported. Review the messages below the editor." if result.warnings else None)

    def save_go(self):
        content = self.output.get("1.0", "end-1c")
        if not content.strip():
            self.status.set("Nothing to save — compile a model first.")
            self._set_log("SAVE INFO\nNo generated Go code is available yet.", "warning")
            self._dialog("Nothing to save yet", "Compile a model first. The generated Go code will appear in the output panel.", "info")
            return
        path = filedialog.asksaveasfilename(
            parent=self,
            title="Save generated Go source",
            defaultextension=".go",
            filetypes=[("Go source", "*.go"), ("All files", "*.*")]
        )
        if not path:
            self.status.set("Save cancelled.")
            self._set_log("Save operation cancelled by user.", "info")
            return
        try:
            with open(path, "w", encoding="utf-8", newline="\n") as f:
                f.write(content + "\n")
            filename = os.path.basename(path)
            self.status.set(f"Saved successfully: {filename}")
            self._set_log(f"SAVE SUCCESS\nGo source saved to: {path}", "success")
            self._dialog("File saved successfully", f"Your generated Go source has been saved.\n\nFile: {filename}",
                         "success", path)
        except OSError as exc:
            self.status.set("Save failed — check the destination and permissions.")
            self._set_log("SAVE ERROR\n" + str(exc), "error")
            self._dialog("Could not save file", "The Go source could not be saved. Check the folder and file permissions.",
                         "error", str(exc))


def main():
    CompilerApp().mainloop()
