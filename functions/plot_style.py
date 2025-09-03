import tkinter as tk
from tkinter import ttk
import matplotlib as mpl

# Mögliche Schriftarten
FONT_OPTIONS = ["Computer Modern", "Times New Roman", "Arial", "Helvetica"]

# Mögliche font.family Werte
FONT_FAMILY_OPTIONS = ["serif", "sans-serif", "monospace", "cursive"]

# Mögliche MathText-Fontsets
MATHTEXT_OPTIONS = ["cm", "dejavusans", "dejavuserif", "stix", "stixsans"]

# Standard-Stile
PLOT_STYLES = {
    "Thesis": {
        "usetex": False,
        "font": "Computer Modern",
        "font.family": "serif",
        "mathtext.fontset": "cm",
        "axes.labelsize": 14,
        "axes.titlesize": 16,
        "xtick.labelsize": 13,
        "ytick.labelsize": 13,
        "legend.fontsize": 13,
        "lines.linewidth": 1.5,
        "figure.dpi": 600,
    },
    "PowerPoint": {
        "usetex": False,
        "font": "Arial",
        "font.family": "sans-serif",
        "mathtext.fontset": "cm",
        "axes.labelsize": 22,
        "axes.titlesize": 24,
        "xtick.labelsize": 20,
        "ytick.labelsize": 20,
        "legend.fontsize": 20,
        "lines.linewidth": 2,
        "figure.dpi": 600,
    },
    "UVVis": {
        "usetex": False,
        "font": "Arial",
        "font.family": "sans-serif",
        "mathtext.fontset": "cm",
        "axes.labelsize": 22,
        "axes.titlesize": 24,
        "xtick.labelsize": 20,
        "ytick.labelsize": 20,
        "legend.fontsize": 20,
        "lines.linewidth": 2,
        "figure.dpi": 600,
    }
}

# Globale Variablen für die Widgets
entries = {}
usetex_var = None
font_var = None
font_family_var = None
mathtext_var = None
mathtext_label = None
mathtext_menu = None
params_frame = None

def toggle_mathtext_visibility():
    if usetex_var.get():
        mathtext_label.grid_remove()
        mathtext_menu.grid_remove()
    else:
        mathtext_label.grid()
        mathtext_menu.grid()

def load_style(style_name):
    global usetex_var, font_var, font_family_var, mathtext_var, mathtext_label, mathtext_menu

    for widget in params_frame.winfo_children():
        widget.destroy()
    entries.clear()

    params = PLOT_STYLES[style_name]

    row = 0
    # LaTeX Toggle
    tk.Label(params_frame, text="Use LaTeX for text rendering").grid(row=row, column=0, sticky="w", padx=5, pady=2)
    usetex_var = tk.BooleanVar(value=params.get("usetex", False))
    cb = tk.Checkbutton(params_frame, variable=usetex_var, command=toggle_mathtext_visibility)
    cb.grid(row=row, column=1, sticky="w", padx=5, pady=2)
    entries["usetex"] = usetex_var
    row += 1

    # Font Dropdown
    tk.Label(params_frame, text="Font").grid(row=row, column=0, sticky="w", padx=5, pady=2)
    font_var = tk.StringVar(value=params.get("font", "Arial"))
    font_menu = ttk.Combobox(params_frame, textvariable=font_var, values=FONT_OPTIONS, state="readonly")
    font_menu.grid(row=row, column=1, padx=5, pady=2)
    entries["font"] = font_var
    row += 1

    # font.family Dropdown
    tk.Label(params_frame, text="Font Family").grid(row=row, column=0, sticky="w", padx=5, pady=2)
    font_family_var = tk.StringVar(value=params.get("font.family", "serif"))
    font_family_menu = ttk.Combobox(params_frame, textvariable=font_family_var, values=FONT_FAMILY_OPTIONS, state="readonly")
    font_family_menu.grid(row=row, column=1, padx=5, pady=2)
    entries["font.family"] = font_family_var
    row += 1

    # MathText Fontset Dropdown
    mathtext_label = tk.Label(params_frame, text="MathText Fontset")
    mathtext_label.grid(row=row, column=0, sticky="w", padx=5, pady=2)
    mathtext_var = tk.StringVar(value=params.get("mathtext.fontset", "cm"))
    mathtext_menu = ttk.Combobox(params_frame, textvariable=mathtext_var, values=MATHTEXT_OPTIONS, state="readonly")
    mathtext_menu.grid(row=row, column=1, padx=5, pady=2)
    entries["mathtext.fontset"] = mathtext_var
    row += 1

    # Zahlen-Parameter
    for label, key in [
        ("Label size", "axes.labelsize"),
        ("Title size", "axes.titlesize"),
        ("X-axis size", "xtick.labelsize"),
        ("Y-axis size", "ytick.labelsize"),
        ("Legend size", "legend.fontsize"),
        ("Line width", "lines.linewidth"),
        ("Resolution (dpi)", "figure.dpi"),
    ]:
        tk.Label(params_frame, text=label).grid(row=row, column=0, sticky="w", padx=5, pady=2)
        entry = tk.Entry(params_frame, width=10)
        entry.insert(0, str(params.get(key, "")))
        entry.grid(row=row, column=1, padx=5, pady=2)
        entries[key] = entry
        row += 1

    toggle_mathtext_visibility()

def apply_style(window):
    new_params = {}

    if entries["usetex"].get():
        new_params["text.usetex"] = True
        new_params["font.family"] = entries["font.family"].get()
        if new_params["font.family"] == "serif":
            new_params["font.serif"] = [entries["font"].get()]
        elif new_params["font.family"] == "sans-serif":
            new_params["font.sans-serif"] = [entries["font"].get()]
    else:
        new_params["text.usetex"] = False
        new_params["font.family"] = entries["font.family"].get()
        if new_params["font.family"] == "serif":
            new_params["font.serif"] = [entries["font"].get()]
        elif new_params["font.family"] == "sans-serif":
            new_params["font.sans-serif"] = [entries["font"].get()]
        new_params["mathtext.fontset"] = entries["mathtext.fontset"].get()

    # Zahlenwerte
    for key in [
        "axes.labelsize",
        "axes.titlesize",
        "xtick.labelsize",
        "ytick.labelsize",
        "legend.fontsize",
        "lines.linewidth",
        "figure.dpi",
    ]:
        try:
            val = float(entries[key].get())
            if val.is_integer():
                val = int(val)
            new_params[key] = val
        except ValueError:
            pass

    mpl.rcParams.update(new_params)
    print("Applied parameters:")
    for k, v in new_params.items():
        print(f"  {k}: {v}")

    window.destroy()
    return

def open_style_tool(master, default_style="Thesis"):
    global params_frame

    window = tk.Toplevel(master)
    window.title("Matplotlib Style Tool")

    # Style-Auswahl Combobox
    style_var = tk.StringVar(value=default_style)
    style_menu = ttk.Combobox(window, textvariable=style_var, values=list(PLOT_STYLES.keys()), state="readonly")
    style_menu.grid(row=0, column=0, padx=10, pady=5)

    load_btn = ttk.Button(window, text="Load style", command=lambda: load_style(style_var.get()))
    load_btn.grid(row=0, column=1, padx=10)

    params_frame = ttk.Frame(window)
    params_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=10, pady=10)

    # Lade den gewünschten Default-Style direkt beim Start
    load_style(default_style)

    apply_btn = ttk.Button(window, text="Apply & Close", command=lambda: apply_style(window))
    apply_btn.grid(row=2, column=0, columnspan=2, pady=10)

    # Modal Verhalten
    window.grab_set()
    window.wait_window()

