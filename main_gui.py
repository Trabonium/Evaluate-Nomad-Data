import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import requests
import pandas as pd 
import os, sys
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

# Globale Variablen
selected_file_path = None
data = None
stats = None
best = None
token = None
directory = None
file_name = None
nomad_url = "http://elnserver.lti.kit.edu/nomad-oasis/api/v1"


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
        show_auto_close_message("Login Successfully", f"Logged in as {username}", 2000)
    except requests.exceptions.RequestException as e:
        messagebox.showerror("Login Failed", f"Error: {e}")

# Datei auswählen
def select_file():
    global selected_file_path
    selected_file_path = filedialog.askopenfilename(title="Choose Excel-file", filetypes=[("Excel-Dateien", "*.xlsx")])
    file_path_label.config(text=f"Chosen data: {selected_file_path}" if selected_file_path else "No data chosen")

# Daten laden
def load_data():
    global data
    if not selected_file_path:
        messagebox.showerror("Error", "Please choose Excel first.")
        return
    try:
        data = get_data_excel_to_df(selected_file_path, nomad_url, token)
        print(data)
        print(data.columns)
        show_auto_close_message("Success", "Data loaded!", 2000)
    except Exception as e:
        messagebox.showerror("Error", f"Data could not be loaded: {e}")

# Daten filtern
def filter_data():
    global filtered_data, data
    if data is None:
        messagebox.showerror("Error", "Please load your data first!")
        return
    try:
        filtered_data, _ = main_filter(data, master=root)
        print(filtered_data)
        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(-1 * (e.delta // 120), "units"))  # Für Windows
        show_auto_close_message("Success", "Data filtered!", 2000)
    except Exception as e:
        messagebox.showerror("Error", f"Filtering gone wrong: {e}")

# Statistiken berechnen
def calculate_stats():
    global stats, data, filtered_data, best
    if data is None:
        messagebox.showerror("Error", "Please load data first!")
        return
    try:
        stats, best = calculate_statistics(filtered_data if 'filtered_data' in globals() else data)
        show_auto_close_message("Sucess", "Statistics calculated successfully!")
    except Exception as e:
        messagebox.showerror("Error", f"Calculate statistics gone wrong: {e}")

# CSV-Export-Funktionen
def csv_raw_export():
    if data is None:
        messagebox.showerror("Error", "Please load data first!")
        return
    path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV-Dateien", "*.csv")])
    if path:
        generate_csv_raw_file(path, data)
        show_auto_close_message("Success", f"CSV file saved: {path}", 2000)

def csv_filtered_export():
    if 'filtered_data' not in globals():
        messagebox.showerror("Error", "Please filter data first!")
        return
    path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV-Dateien", "*.csv")])
    if path:
        generate_csv_filtered_file(path, filtered_data, data, None)
        show_auto_close_message("Success", f"CSV file saved: {path}", 2000)

def filter_page_2():
    global filtered_data, data
    if data is None:
        messagebox.showerror("Error", "Please load your data first!")
        return
    try:
        filtered_data = freier_filter(data, master=root)

        #ausgabe der gefilterten daten
        common_cols = list(data.columns.intersection(filtered_data.columns))
        df_diff = data.merge(filtered_data, on=common_cols, how='left', indicator=True)
        df_A_only = df_diff[df_diff['_merge'] == 'left_only'].drop(columns=['_merge'])
        print(df_A_only)

        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(-1 * (e.delta // 120), "units"))  # Für Windows
        show_auto_close_message("Success", "Data filtered!", 2000)
    except Exception as e:
        messagebox.showerror("Error", f"Filtering gone wrong: {e}")

def merge_UVVis_files():
    try:
        UVVis_merge(master=root)
        show_auto_close_message("Success", "Back to the normal window!", 2000)
    except:
        messagebox.showerror("Error", "Something went wrong with the UVVis merging.")

def Rename_folders_and_measurements():
    try:
        Renaming_folders(master=root)
        show_auto_close_message("Success", "Back to the normal window!", 2000)
    except:
        messagebox.showerror("Error", "Something went wrong with the renaming.")

def excel_creator_function():
    try:
        Excel_GUI(master=root)
        show_auto_close_message("Success", "Back to the normal window!", 2000)
    except:
        messagebox.showerror("Error", "Something went wrong with the Excel creator.")

def EQE_Joshua():
    try:
        GUI_fuer_Joshuas_EQE(master=root)
        show_auto_close_message("Success", "Back to the normal window!", 2000)
    except:
        messagebox.showerror("Error", "Something went wrong with the EQE plotting.")

def Rename_JV_files():
    try:
        measurement_file_organizer(master=root)
        show_auto_close_message("Success", "Back to the normal window!", 2000)
    except:
        messagebox.showerror("Error", "Something went wrong with the JV file renaming.")

def generate_report():
    global data, stats, directory, file_name, filtered_data, best

    if data is None or stats is None:
        messagebox.showerror("Error", "Please load data and calculate statistics first.")
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
    }

    file_path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF files", "*.pdf")])
    if not file_path:
        return

    try:
        directory, file_name = generate_pdf_report(filtered_data, stats, best, selected_plots_uebergeben, file_path, nomad_url, token)
        show_auto_close_message("Success", f"PDF report with filtered data saved to: {file_path}", 2000)
    except:
        try:
            directory, file_name = generate_pdf_report(data, stats, best, selected_plots_uebergeben, file_path, nomad_url, token)
            show_auto_close_message("Success", f"PDF report with raw data saved to: {file_path}", 2000)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate report: {e}")


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
        plot_options_frame.grid(row=14, column=0, pady=5, sticky="n")  # Wieder anzeigen
        toggle_button.config(text="▼ Hide Plot Options")


# Hauptfenster erstellen
root = tk.Tk()
root.title("Script for NOMAD data evaluation")
root.geometry("600x600")
#root.iconbitmap(os.path.join(os.path.dirname(__file__), "GUI.ico"))


# Styling mit ttk
style = ttk.Style()
style.configure("TButton", font=("Arial", 10), padding=5)
style.configure("Hover.TButton", background="lightblue")
style.configure("TCheckbutton", font=("Arial", 10))
style.configure("Hover.TCheckbutton", background="lightgray")

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
    ("Select File", select_file, "Choose Excel file to download your wanted data. If you need data from multiple batches, merge your experimental Planning excel files - but DO NOT UPLOAD TO NOMAD TWICE!"),
    ("Load corresponding Data from NOMAD OASIS", load_data, "Download data with the choosen Excel file.")
]

row_index = 3
for text, command, tooltip in buttons_info1:
    if row_index == 5:
        row_index += 1
    btn = ttk.Button(scrollable_frame, text=text, command=command)
    btn.grid(row=row_index, column=0, pady=5)
    apply_hover_effect(btn, "TButton", "Hover.TButton")
    
    help_label = tk.Label(scrollable_frame, text="❓", fg="gray", cursor="hand2")
    help_label.grid(row=row_index, column=1, padx=5)
    help_label.bind("<Enter>", lambda e, t=tooltip: show_tooltip(e, t))
    help_label.bind("<Leave>", hide_tooltip)
    
    row_index += 1


file_path_label = ttk.Label(scrollable_frame, text="data path: ", foreground="gray")
file_path_label.grid(row=5, column=0, pady=5)

notebook = ttk.Notebook(scrollable_frame)
frame1 = ttk.Frame(notebook)
frame2 = ttk.Frame(notebook)
frame3 = ttk.Frame(notebook)

for frame in [frame1, frame2, frame3]:
    frame.columnconfigure(0, weight=1)  # zentriert  alle objekte die in den frames drin sind


notebook.add(frame1, text="solar cell data evaluation")
notebook.add(frame2, text="halfstack data evaluation")
notebook.add(frame3, text="tools")
notebook.grid(row=7, column=0, columnspan=2, pady=10, sticky="ew")


buttons_info2 = [ #buttons für das erste notebook
    ("Filter your data", filter_data, "Filter your data if wished (optional and repeatable)."),
    ("Calculate Statistics", calculate_stats, "Calculate the statistics of your data."),
    ("Generate CSV (raw data)", generate_csv_raw_file, "Export your raw data as csv (optional and repeatable)."),
    ("Generate CSV (filtered data)", generate_csv_filtered_file, "Export your filtered data as csv (optional and repeatable)."),
    ("Generate Report", generate_report, "Export your report with your wished plots and informations (optional and repeatable).")
]

row_index = 8
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
toggle_button.grid(row=13, column=0, pady=10)  # Stelle sicher, dass der Button über den Optionen bleibt

apply_hover_effect(toggle_button, "TButton", "Hover.TButton")

# Frame für Checkboxen (zunächst versteckt)
plot_options_frame = tk.Frame(frame1)
plot_options_frame.grid(row=14, column=0, pady=5, sticky="n")
plot_options_frame.grid_remove()

# Checkbox-Variablen für Plots
jv_var = tk.BooleanVar(value=True)
box_var = tk.BooleanVar(value=True)
separate_scan_var = tk.BooleanVar(value=True)
hysteresis = tk.BooleanVar(value=False)
eqe_var = tk.BooleanVar(value=False)
mpp_var = tk.BooleanVar(value=False)
table_var = tk.BooleanVar(value=True)
picture_var = tk.BooleanVar(value=True)

# Checkboxen
plot_options = [
    ("JV Curves", jv_var, "Plots the median and best JVs for each variation."),
    ("Box + Scatter Plots", box_var, "Plots the box and scatter plots for your batch statistics."),
    ("Separate Backwards/Forwards", separate_scan_var, "Adds the reverse and forwards differentiation to your box and scatter plots."),
    ("Hysteresis plot", hysteresis, "Plots the hysteresis as a box + scatter plot."),
    ("EQE Curves", eqe_var, "Plot EQE data."),
    ("MPP Curves", mpp_var, "Plots the MPP tracking."),
    ("Data Table", table_var, "Adds a table with the most important informations to your PDF."), 
    ("Generate pictures", picture_var, "Generates extra pictures of the plots.")
]

for idx, (text, var, tooltip) in enumerate(plot_options):
    check = ttk.Checkbutton(plot_options_frame, text=text, variable=var, style="TCheckbutton")
    check.grid(row=idx, column=0, sticky="w", padx=10)
    apply_hover_effect(check, "TCheckbutton", "Hover.TCheckbutton")
    check.bind("<Enter>", lambda e, t=tooltip: show_tooltip(e, t))
    check.bind("<Leave>", hide_tooltip)

#ende frame no 1

buttons_info3 = [ #buttons für frame 2
    ("Halfstack filter", filter_page_2, "Filter your data if wished (optional and repeatable).")
]

row_index = 1
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
    ("Rename JV files", Rename_JV_files, "Use a script to rename your JV files to the correct NOMAD format.")
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
path_to_credentials = os.path.dirname(os.path.abspath(sys.argv[0])) + "\\Bayesian_Optimization\\bayesian-optimization\\conf"
conf_loader = OmegaConfigLoader(conf_source=path_to_credentials)
credentials = conf_loader["credentials"]
if credentials.__contains__('nomad_db'):
    username_entry.insert(0,credentials['nomad_db']['username'])
    password_entry.insert(0,credentials['nomad_db']['password'])
    show_auto_close_message('Credentials loaded!', 'Credentials loaded from file.\nYou still need to press Login')

root.mainloop()