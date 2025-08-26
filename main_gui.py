import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinterdnd2 import DND_FILES, TkinterDnD #drag and drop window
import requests
import pandas as pd 
import os, sys
import numpy as np

if not getattr(sys, 'frozen', False):  #only import in development environment
    from kedro.config import OmegaConfigLoader
    from kedro.framework.project import settings

from functions.get_data import get_data_excel_to_df
from functions.calculate_statistics import calculate_statistics
from functions.generate_report import generate_pdf_report
from functions.generate_csv_data import generate_csv_raw_file, generate_csv_filtered_file
from functions.schieberegler import main_filter
from functions.freier_filter import freier_filter
from functions.UVVis_merge_Eln import UVVis_merge
from functions.Renaming_Measurements_and_Folders import Renaming_folders
from functions.Create_Excel_GUI_2 import Excel_GUI
from functions.EQE_Joshua_extern import GUI_fuer_Joshuas_EQE
from functions.rename_JV_Daniel import measurement_file_organizer
from functions.Tandem_Puri_JV_split import tandem_puri_jv_split
from functions.UVVis_plotting import UVVis_plotting     

#spinner imports
from PIL import Image, ImageTk, ImageSequence, ImageOps
import threading
from pathlib import Path

# Globale Variablen für Spinner
frames = []
gif_label = None
status_label = None
animating = False
current_frame_index = 0

# Globale Variablen
selected_file_path = None
data = None
filtered_data = None
stats = None
best = None
token = None
directory = None
file_name = None
filter_cycle_boolean = None
nomad_url = "http://elnserver.lti.kit.edu/nomad-oasis/api/v1"
uvvis_unit_mode = "wavelength" # default for UVVis plotting


def show_auto_close_message(title, message, timeout=3000):
    msg_window = tk.Toplevel()
    msg_window.title(title)
    msg_window.geometry("300x100")
    
    label = ttk.Label(msg_window, text=message, wraplength=280)
    label.pack(expand=True, padx=10, pady=10)
    
    msg_window.after(timeout, msg_window.destroy)  # Auto close after timeout (in ms)
    msg_window.mainloop()


# Login-Funktion
def login_handler():
    def task_login_handler():
        global token
        username = username_entry.get()
        password = password_entry.get()
        if not username or not password:
            messagebox.showerror("Error", "Please insert name and password.")
            return
        try:
            response = requests.get(f"{nomad_url}/auth/token", params={"username": username, "password": password})
            response.raise_for_status()
            token = response.json().get('access_token', None)
        except requests.exceptions.RequestException as e:
            root.after(0, lambda : messagebox.showerror("Login Failed", f"Error: {e}"))
    run_with_spinner(task_login_handler)

# Datei auswählen
def select_file():
    def task_select_file():
        global selected_file_path
        selected_file_path = filedialog.askopenfilename(title="Choose Excel-file", filetypes=[("Excel-Dateien", "*.xlsx")])
        file_path_label.config(text=f"Chosen data: {selected_file_path}" if selected_file_path else "No data chosen")
    run_with_spinner(task_select_file)

#drag and drop select file function
def handle_drop(event):
    global selected_file_path
    path = event.data.strip('{}')  # Bei Leerzeichen im Pfad
    if path.endswith('.xlsx'):
        selected_file_path = path
        file_path_label.config(text=f"Chosen data: {selected_file_path}")
    else:
        file_path_label.config(text="❌ Not an Excel file!")

    
def load_data():
    def task_load_data():
        global data, filtered_data, filter_cycle_boolean
        if not selected_file_path:
            messagebox.showerror("Error", "Please choose Excel first.")
            return
        try:
            #columns to check for 'nan' strings, that are not interpreted as NaN
            cols = ["efficiency", "fill_factor", "open_circuit_voltage", "short_circuit_current_density"]
            data = get_data_excel_to_df(selected_file_path, nomad_url, token)
            data[cols] = data[cols].replace('nan', np.nan)
            
            #reset values for new loaded data
            filtered_data = None
            filter_cycle_boolean = None
        except Exception as e:
            try:
                root.after(0, lambda : messagebox.showerror("Error", f"Data could not be loaded: {e}"))
            except: 
                root.after(0, lambda : messagebox.showerror("Error", "Data could not be loaded."))
    run_with_spinner(task_load_data)

# Daten filtern
def filter_data():
    def task_filter_data():
        global filtered_data, data, filter_cycle_boolean
        if data is None:
            messagebox.showerror("Error", "Please load your data first!")
            return
        try:
            filtered_data, _, filter_cycle_boolean = main_filter(data, master=root)
            #print(filtered_data)
            canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(-1 * (e.delta // 120), "units"))  # Für Windows
        except Exception as e:
            root.after(0, lambda : messagebox.showerror("Error", f"Filtering gone wrong: {e}"))
    run_with_spinner(task_filter_data)

# Statistiken berechnen
def calculate_stats():
    def task_calculate_stats():
        global stats, data, filtered_data, best
        if data is None:
            messagebox.showerror("Error", "Please load data first!")
            return
        try:
            stats, best = calculate_statistics(filtered_data if filtered_data is not None else data)
        except Exception as e:
            root.after(0, lambda : messagebox.showerror("Error", f"Calculate statistics gone wrong: {e}"))
    run_with_spinner(task_calculate_stats)

# CSV-Export-Funktionen
def csv_raw_export():
    def task_csv_raw_export():
        if data is None:
            root.after(0, lambda : messagebox.showerror("Error", f"Please load data first!: {e}"))
            return
        else:
            path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV-Dateien", "*.csv")])
            if path:
                generate_csv_raw_file(path, data)
    run_with_spinner(task_csv_raw_export)

def csv_filtered_export():
    def task_csv_filtered_export():
        if filtered_data is None:
            root.after(0, lambda : messagebox.showerror("Error", f"Please filter data first!: {e}"))
            return
        else:
            path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV-Dateien", "*.csv")])
            if path:
                generate_csv_filtered_file(path, filtered_data, data, None)
    run_with_spinner(task_csv_filtered_export)

def free_filter_for_halfstacks():
    def task_free_filter_for_halfstacks():
        global filtered_data, data
        if data is None:
            root.after(0, lambda : messagebox.showerror("Error", f"Please load your data first!: {e}"))
            return
        try:
            filtered_data = freier_filter(data, master=root)

            #ausgabe der gefilterten daten
            #common_cols = list(data.columns.intersection(filtered_data.columns))
            #df_diff = data.merge(filtered_data, on=common_cols, how='left', indicator=True)
            #df_A_only = df_diff[df_diff['_merge'] == 'left_only'].drop(columns=['_merge'])
            #print(df_A_only)

            canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(-1 * (e.delta // 120), "units"))  # Für Windows
        except Exception as e:
            root.after(0, lambda : messagebox.showerror("Error", f"Filtering gone wrong: {e}"))
    run_with_spinner(task_free_filter_for_halfstacks)

def UVVis_plotting_function():
    def task_UVVis_plotting_function():
        global filtered_data, data, nomad_url, token, uvvis_unit_mode
        #check if data is loaded
        if data is None:
            root.after(0, lambda : messagebox.showerror("Error", f"Please load your data first!: {e}"))
            return
        #get place to save the plot
        file_path = filedialog.asksaveasfilename(
            defaultextension=".svg",
            filetypes=[("SVG files", "*.svg")]
        )
        #check if user has chosen a file
        if not file_path:
            return

        #data_to_plot = data if filtered_data is None else filtered_data
        data_to_plot = filtered_data if filtered_data is not None else data

        try:
            UVVis_plotting(data_to_plot, file_path, nomad_url, token, unit = uvvis_unit_mode)
        except Exception as e:
            root.after(0, lambda : messagebox.showerror("Error", f"UVVis plotting gone wrong: {e}"))
    run_with_spinner(task_UVVis_plotting_function)

def toggle_uvvis_unit():
    global uvvis_unit_mode
    if uvvis_unit_mode == "wavelength":
        uvvis_unit_mode = "photon_energy"
        uvvis_toggle_button.config(text="photon energy [eV]")
    elif uvvis_unit_mode == "photon_energy":
        uvvis_unit_mode = "tauc_plot"
        uvvis_toggle_button.config(text="Tauc plot (for 550 nm thickness)")
    else:  
        uvvis_unit_mode = "wavelength"
        uvvis_toggle_button.config(text="wavelength [nm]")


def merge_UVVis_files():
    def task_merge_UVVis_files():
        try:
            UVVis_merge(master=root)
        except:
            root.after(0, lambda : messagebox.showerror("Error", "Something went wrong with the UVVis merging."))
    run_with_spinner(task_merge_UVVis_files)

def Rename_folders_and_measurements():
    def task_Rename_folders_and_measurements():
        try:
            Renaming_folders(master=root)
        except:
            root.after(0, lambda : messagebox.showerror("Error", "Something went wrong with the renaming."))
    run_with_spinner(task_Rename_folders_and_measurements)

def excel_creator_function():
    def task_excel_creator_function():
        try:
            Excel_GUI(master=root)
        except:
            root.after(0, lambda : messagebox.showerror("Error", "Something went wrong with the Excel creator."))
    run_with_spinner(task_excel_creator_function)

def EQE_Joshua():
    def task_EQE_Joshua():
        try:
            GUI_fuer_Joshuas_EQE(master=root)
        except:
            root.after(0, lambda : messagebox.showerror("Error", "Something went wrong with the EQE plotting."))
    run_with_spinner(task_EQE_Joshua)

def Rename_JV_files():
    def task_Rename_JV_files():
        try:
            measurement_file_organizer(master=root)
        except:
            root.after(0, lambda : messagebox.showerror("Error", "Something went wrong with the JV file renaming."))
    run_with_spinner(task_Rename_JV_files)

def spilt_puri_tandem_files():
    def task_spilt_puri_tandem_files():
        try:
            tandem_puri_jv_split(master=root)
        except Exception as e:
            root.after(0, lambda : messagebox.showerror("Error", f"Something went wrong with the tandem splitting: {e}"))
    run_with_spinner(task_spilt_puri_tandem_files)

def generate_report():
    def task_generate_report():
        global data, stats, directory, file_name, filtered_data, best, filter_cycle_boolean

        if data is None or stats is None:
            root.after(0, lambda : messagebox.showerror("Error", "Please load data and calculate statistics first."))
            return

        # Hier wird `selected_plots` aus den Checkbox-Variablen aktualisiert
        selected_plots_uebergeben = {
            "JV": jv_var.get(),
            "Box+Scatter": box_var.get(),
            "SeparateScan": separate_scan_var.get(), 
            "Hysteresis": hysteresis.get(),
            "EQE": eqe_var.get(),
            "MPP": mpp_var.get(),
            "Table": table_var.get(), 
            "Picture": picture_var.get(),
            "Latex": latex_var.get(),
        }

        file_path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF files", "*.pdf")])
        if not file_path:
            return

        try:
            directory, file_name = generate_pdf_report(filtered_data, stats, best, selected_plots_uebergeben, file_path, nomad_url, token, filter_cycle_boolean)
        except:
            try:
                directory, file_name = generate_pdf_report(data, stats, best, selected_plots_uebergeben, file_path, nomad_url, token,filter_cycle_boolean)
            except Exception as e:
                root.after(0, lambda : messagebox.showerror("Error", f"Failed to generate report: {e}"))
    run_with_spinner(task_generate_report)

# Funktion für Hover-Effekt für Buttons und Checkbuttons
def apply_hover_effect(widget, normal_style, hover_style):
    if isinstance(widget, ttk.Widget):  
        widget.bind("<Enter>", lambda e: widget.configure(style=hover_style))
        widget.bind("<Leave>", lambda e: widget.configure(style=normal_style))
    else:  
        widget.bind("<Enter>", lambda e: widget.config(bg="lightgray"))
        widget.bind("<Leave>", lambda e: widget.config(bg="SystemButtonFace"))

# Funktion für Tooltips
def show_tooltip(event, text):
    """Zeigt einen Tooltip mit dem gegebenen Text an"""
    global tooltip_window
    x, y, _, _ = event.widget.bbox("insert")
    x += event.widget.winfo_rootx() + 25
    y += event.widget.winfo_rooty() + 25
    tooltip_window = tk.Toplevel(event.widget)
    tooltip_window.wm_overrideredirect(True)
    tooltip_window.geometry(f"+{x}+{y}")
    label = tk.Label(tooltip_window, text=text, background="lightyellow", relief="solid", borderwidth=1)
    label.pack()

def hide_tooltip(event):
    """Versteckt den Tooltip"""
    global tooltip_window
    if tooltip_window:
        tooltip_window.destroy()
        tooltip_window = None

# Toggle-Funktion für Plot-Optionen
def toggle_plot_options():
    if plot_options_frame.winfo_ismapped():
        plot_options_frame.grid_remove()  # Nur das Frame verstecken
        toggle_button.config(text="▶ Show Plot Options")  # Button bleibt sichtbar
    else:
        plot_options_frame.grid(row=15, column=0, pady=5, sticky="n")  # Wieder anzeigen
        toggle_button.config(text="▼ Hide Plot Options")


# Hauptfenster erstellen
root = TkinterDnD.Tk()
root.title("Script for NOMAD data evaluation")
root.geometry("600x600")
#root.iconbitmap(os.path.join(os.path.dirname(__file__), "GUI.ico"))

# Spinner functions
# get the spinner
def resource_path(relative_path):
    """Gibt den Pfad zur Datei zurück – kompatibel mit .exe (PyInstaller)."""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path) #in case of .exe
    return os.path.join(os.path.abspath("."), relative_path) #in case of programming mode

def init_spinner_ui(master):
    global gif_label, status_label, frames

    TARGET_SIZE = (100, 100)

    try:
        gif_path = resource_path("giffolder/spinner.gif")
        gif = Image.open(gif_path)
        frames.clear()  # falls neu initialisiert

        for frame in ImageSequence.Iterator(gif):
            frame_resized = frame.copy().convert("RGBA").resize(TARGET_SIZE, Image.LANCZOS)
            frames.append(ImageTk.PhotoImage(frame_resized))

        gif_label.config(image=frames[0])
    except Exception as e:
        print("Fehler beim Laden von spinner.gif:", e)

# === Spinner-Steuerung ===
def show_spinner():
    global animating
    animating = True
    status_label.config(text="Working...", style="StatusWorking.TLabel")
    update_spinner_frame(current_frame_index)  # ✅ Starte dort, wo zuletzt aufgehört

def update_spinner_frame(idx):
    global current_frame_index
    if not animating or not frames:
        return
    gif_label.config(image=frames[idx])
    gif_label.image = frames[idx]  # Referenz halten
    current_frame_index = idx      # 🧠 Merke den aktuellen Frame
    root.after(100, update_spinner_frame, (idx + 1) % len(frames))

def hide_spinner():
    global animating
    animating = False
    status_label.config(text="Done", style="StatusReady.TLabel")

# === Wrapper-Funktion für lange Aufgaben ===
def run_with_spinner(task_function):
    def task():
        try:
            task_function()
        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            root.after(0, hide_spinner)
    show_spinner()
    threading.Thread(target=task, daemon=True).start()

# Styling mit ttk
style = ttk.Style()
style.configure("TButton", font=("Arial", 10), padding=5)
style.configure("Hover.TButton", background="lightblue")
style.configure("TCheckbutton", font=("Arial", 10))
style.configure("Hover.TCheckbutton", background="lightgray")
style.configure("StatusReady.TLabel", foreground="green")
style.configure("StatusWorking.TLabel", foreground="orange")


# Haupt-Frame mit Scroll-Funktion
main_frame = tk.Frame(root)
main_frame.pack(fill=tk.BOTH, expand=True)

canvas = tk.Canvas(main_frame)
scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=canvas.yview)
scrollable_frame = ttk.Frame(canvas)

def update_scrollregion(event=None):
    scrollable_frame.update_idletasks()  # Stellt sicher, dass alle Widgets gerendert wurden
    canvas.configure(scrollregion=canvas.bbox("all"))  # Setzt die Scrollregion korrekt

scrollable_frame.bind("<Configure>", update_scrollregion)


window_id = canvas.create_window((0, 0), window=scrollable_frame, anchor="center")
def update_canvas_size(event):
    canvas.itemconfig(window_id, width=canvas.winfo_width())
    update_scrollregion()  # Scrollregion erneut setzen

canvas.bind("<Configure>", update_canvas_size)

canvas.configure(yscrollcommand=scrollbar.set)
canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(-1 * (e.delta // 120), "units"))

scrollable_frame.columnconfigure(0, weight=1)

# Login-Eingabe
ttk.Label(scrollable_frame, text="NOMAD Login (name and password)", font=("Helvetica", 12, "bold")).grid(row=0, column=0, pady=5, sticky="n")

username_entry = ttk.Entry(scrollable_frame, width=30)
username_entry.grid(row=1, column=0, pady=5)

password_entry = ttk.Entry(scrollable_frame, width=30, show="*")
password_entry.grid(row=2, column=0, pady=5)

# Fragezeichen für Login-Felder
username_help = tk.Label(scrollable_frame, text="❓", fg="gray", cursor="hand2")
username_help.grid(row=1, column=1, padx=5)
username_help.bind("<Enter>", lambda e: show_tooltip(e, "Please insert your NOMAD name or email here."))
username_help.bind("<Leave>", hide_tooltip)

password_help = tk.Label(scrollable_frame, text="❓", fg="gray", cursor="hand2")
password_help.grid(row=2, column=1, padx=5)
password_help.bind("<Enter>", lambda e: show_tooltip(e, "Please insert your NOMAD password here."))
password_help.bind("<Leave>", hide_tooltip)

# Buttons mit tatsächlichen Funktionsaufrufen
buttons_info1 = [ #buttons für die kopfzeile
    ("Login", login_handler, "Click here to log in to the NOMAD oasis."),
    ("Load corresponding Data from NOMAD OASIS", load_data, "Download data with the choosen Excel file.")
]

row_index = 3
for text, command, tooltip in buttons_info1:
    if row_index == 4:
        row_index += 2
    btn = ttk.Button(scrollable_frame, text=text, command=command)
    btn.grid(row=row_index, column=0, pady=5)
    apply_hover_effect(btn, "TButton", "Hover.TButton")
    
    help_label = tk.Label(scrollable_frame, text="❓", fg="gray", cursor="hand2")
    help_label.grid(row=row_index, column=1, padx=5)
    help_label.bind("<Enter>", lambda e, t=tooltip: show_tooltip(e, t))
    help_label.bind("<Leave>", hide_tooltip)
    
    row_index += 1

# Zeile im Grid für Button + Dropfeld
row_index = 4  # z. B. anpassen, je nachdem wo du bist

# Frame für Button + Drag-Drop
file_frame = ttk.Frame(scrollable_frame)
file_frame.grid(row=4, column=0, columnspan=2, pady=5, sticky="n")

# Button
select_button = ttk.Button(file_frame, text="Select File", command=select_file)
select_button.grid(row=0, column=0, padx=(0, 10))

drop_label = ttk.Label(file_frame, text="⬇️ Drag & Drop Excel file", relief="ridge", padding=5)
drop_label.grid(row=0, column=1)

apply_hover_effect(select_button, "TButton", "Hover.TButton")

# Drop-Ziel registrieren
drop_label.drop_target_register(DND_FILES)
drop_label.dnd_bind('<<Drop>>', handle_drop)

# Hilfe-Icon separat rechts
file_help = tk.Label(scrollable_frame, text="❓", fg="gray", cursor="hand2")
file_help.grid(row=row_index, column=1, padx=5)
file_help.bind("<Enter>", lambda e: show_tooltip(e, "Choose Excel file or drag it here."))
file_help.bind("<Leave>", hide_tooltip)


file_path_label = ttk.Label(scrollable_frame, text="data path: ", foreground="gray")
file_path_label.grid(row=5, column=0, pady=5)

#spinner positioning
spinner_frame = ttk.Frame(scrollable_frame)
spinner_frame.grid(row=7, column=0, columnspan=2, pady=(5, 5), sticky="ew")
status_label = ttk.Label(spinner_frame, text="Ready", style="StatusReady.TLabel", anchor="center")
status_label.pack()
gif_label = ttk.Label(spinner_frame)
gif_label.pack()

init_spinner_ui(spinner_frame)


notebook = ttk.Notebook(scrollable_frame)
frame1 = ttk.Frame(notebook)
frame2 = ttk.Frame(notebook)
frame3 = ttk.Frame(notebook)

for frame in [frame1, frame2, frame3]:
    frame.columnconfigure(0, weight=1)  # zentriert  alle objekte die in den frames drin sind


notebook.add(frame1, text="solar cell data evaluation")
notebook.add(frame2, text="halfstack data evaluation")
notebook.add(frame3, text="tools")
notebook.grid(row=8, column=0, columnspan=2, pady=10, sticky="ew")


buttons_info2 = [ #buttons für das erste notebook
    ("Filter your data", filter_data, "Filter your data if wished (optional and repeatable)."),
    ("Calculate Statistics", calculate_stats, "Calculate the statistics of your data."),
    ("Generate CSV (raw data)", generate_csv_raw_file, "Export your raw data as csv (optional and repeatable)."),
    ("Generate CSV (filtered data)", generate_csv_filtered_file, "Export your filtered data as csv (optional and repeatable)."),
    ("Generate Report", generate_report, "Export your report with your wished plots and informations (optional and repeatable).")
]

row_index = 9
for text, command, tooltip in buttons_info2:
    btn = ttk.Button(frame1, text=text, command=command)
    btn.grid(row=row_index, column=0, pady=5)
    apply_hover_effect(btn, "TButton", "Hover.TButton")
    
    help_label = tk.Label(frame1, text="❓", fg="gray", cursor="hand2")
    help_label.grid(row=row_index, column=1, padx=5)
    help_label.bind("<Enter>", lambda e, t=tooltip: show_tooltip(e, t))
    help_label.bind("<Leave>", hide_tooltip)
    
    row_index += 1


toggle_button = tk.Button(frame1, text="▶ Show Plot Options", command=toggle_plot_options)
toggle_button.grid(row=14, column=0, pady=10)  # Stelle sicher, dass der Button über den Optionen bleibt

apply_hover_effect(toggle_button, "TButton", "Hover.TButton")

# Frame für Checkboxen (zunächst versteckt)
plot_options_frame = tk.Frame(frame1)
plot_options_frame.grid(row=15, column=0, pady=5, sticky="n")
plot_options_frame.grid_remove()

# Checkbox-Variablen für Plots
jv_var = tk.BooleanVar(value=True)
box_var = tk.BooleanVar(value=True)
separate_scan_var = tk.BooleanVar(value=True)
hysteresis = tk.BooleanVar(value=False)
eqe_var = tk.BooleanVar(value=False)
mpp_var = tk.BooleanVar(value=False)
table_var = tk.BooleanVar(value=True)
picture_var = tk.BooleanVar(value=False)
latex_var = tk.BooleanVar(value=False)

# Checkboxen
plot_options = [
    ("JV Curves", jv_var, "Plots the median and best JVs for each variation."),
    ("Box + Scatter Plots", box_var, "Plots the box and scatter plots for your batch statistics."),
    ("Separate Backwards/Forwards", separate_scan_var, "Adds the reverse and forwards differentiation to your box and scatter plots."),
    ("Hysteresis plot", hysteresis, "Plots the hysteresis as a box + scatter plot."),
    ("EQE Curves", eqe_var, "Plot EQE data - of the best availabe sample for each variation"),
    ("MPP Curves", mpp_var, "Plots the MPP tracking - of the best availabe sample for each variation"),
    ("Data Table", table_var, "Adds a table with the most important informations to your PDF."), 
    ("Generate pictures", picture_var, "Saves all plots as svg vector files additionally to the pdf report."),
    ("Latex text", latex_var, "Renders the text in the plots in LaTeX format (you need a LaTeX distribution installed).")
]

for idx, (text, var, tooltip) in enumerate(plot_options):
    check = ttk.Checkbutton(plot_options_frame, text=text, variable=var, style="TCheckbutton")
    check.grid(row=idx, column=0, sticky="w", padx=10)
    apply_hover_effect(check, "TCheckbutton", "Hover.TCheckbutton")
    check.bind("<Enter>", lambda e, t=tooltip: show_tooltip(e, t))
    check.bind("<Leave>", hide_tooltip)

#ende frame no 1

buttons_info3 = [ #buttons für frame 2
    ("Halfstack filter", free_filter_for_halfstacks, "Filter your data for halfstacks if wished (optional and repeatable)."), 
    ("UVVis plotting", UVVis_plotting_function, "Plot your UVVis data with the band gaps."),
]

uvvis_toggle_button = ttk.Button(frame2, text="wavelength [nm]", command=toggle_uvvis_unit)
uvvis_toggle_button.grid(row=row_index+2, column=0, pady=5, sticky="w")

# Optional: Tooltip & Hover
apply_hover_effect(uvvis_toggle_button, "TButton", "Hover.TButton")
help_label = tk.Label(frame2, text="❓", fg="gray", cursor="hand2")
help_label.grid(row=row_index, column=1, padx=5)
help_label.bind("<Enter>", lambda e: show_tooltip(e, "Toggle between wavelength [nm] and photon energy [eV]."))
help_label.bind("<Leave>", hide_tooltip)

row_index += 1

for text, command, tooltip in buttons_info3:
    btn = ttk.Button(frame2, text=text, command=command)
    btn.grid(row=row_index, column=0, pady=5)
    apply_hover_effect(btn, "TButton", "Hover.TButton")
    
    help_label = tk.Label(frame2, text="❓", fg="gray", cursor="hand2")
    help_label.grid(row=row_index, column=1, padx=5)
    help_label.bind("<Enter>", lambda e, t=tooltip: show_tooltip(e, t))
    help_label.bind("<Leave>", hide_tooltip)
    
    row_index += 1

buttons_info4 = [ #buttons für frame 3
    ("UVVis merge", merge_UVVis_files, "Merge your UVVis R & T files."),
    ("Old data renaming", Rename_folders_and_measurements, "Rename your folders and measurements."),
    ("Excel creator for NOMAD", excel_creator_function, "Create an Excel file for NOMAD."),
    ("Short EQE plotting", EQE_Joshua, "Use a short EQE plotting tool for not uploaded data."),
    ("Rename JV files", Rename_JV_files, "Use a script to rename your JV files to the correct NOMAD format. Adds .jv to the end of the filename and changes the cycle and pixel info to be read properly"), 
    ("Puri JV split", spilt_puri_tandem_files, "Split the Puri files to old JV format.")
]

row_index = 1
for text, command, tooltip in buttons_info4:
    btn = ttk.Button(frame3, text=text, command=command)
    btn.grid(row=row_index, column=0, pady=5)
    apply_hover_effect(btn, "TButton", "Hover.TButton")
    
    help_label = tk.Label(frame3, text="❓", fg="gray", cursor="hand2")
    help_label.grid(row=row_index, column=1, padx=5)
    help_label.bind("<Enter>", lambda e, t=tooltip: show_tooltip(e, t))
    help_label.bind("<Leave>", hide_tooltip)
    
    row_index += 1

#load credentials from credentials.yml in kedro conf
#if you are unsure how to use this, read the top-level readme in Bayesian_Optimization
if not getattr(sys, 'frozen', False):  #only import in development environment
    try:
        path_to_credentials = os.path.dirname(os.path.abspath(sys.argv[0])) + "\\Bayesian_Optimization\\bayesian-optimization\\conf"
        conf_loader = OmegaConfigLoader(conf_source=path_to_credentials)
        credentials = conf_loader["credentials"]
        if 'nomad_db' in credentials:
            username_entry.insert(0, credentials['nomad_db']['username'])
            password_entry.insert(0, credentials['nomad_db']['password'])
            #show_auto_close_message('Credentials loaded!', 'Credentials loaded from file.\nYou still need to press Login')
    except Exception as e:
        print(f"Credentials konnten nicht geladen werden: {e}")

root.mainloop()