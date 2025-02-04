import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import requests
import pandas as pd 

from functions.get_data import get_data_excel_to_df
from functions.calculate_statistics import calculate_statistics
from functions.generate_report import generate_pdf_report
from functions.generate_csv_data import generate_csv_raw_file, generate_csv_filtered_file
from functions.schieberegler import main_filter

# Globale Variablen
selected_file_path = None
data = None
stats = None
token = None
directory = None
file_name = None
nomad_url = "http://elnserver.lti.kit.edu/nomad-oasis/api/v1"

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
        messagebox.showinfo("Login Successfully", f"Logged in as {username}")
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
        messagebox.showinfo("Success", "Data loaded!")
    except Exception as e:
        messagebox.showerror("Error", f"Data could not be loaded: {e}")

# Daten filtern
def filter_data():
    global filtered_data
    if data is None:
        messagebox.showerror("Error", "Please load your data first!")
        return
    try:
        filtered_data, _ = main_filter(data, master=root)
        canvas.bind_all("<MouseWheel>", on_mouse_wheel)  # Für Windows
        messagebox.showinfo("Success", "Data filtered!")
    except Exception as e:
        messagebox.showerror("Error", f"Filtering gone wrong: {e}")

# Statistiken berechnen
def calculate_stats():
    global stats
    if data is None:
        messagebox.showerror("Error", "Please load data first!")
        return
    try:
        stats = calculate_statistics(filtered_data if 'filtered_data' in globals() else data)
        messagebox.showinfo("Error", "Statistics calculated successfully!")
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
        messagebox.showinfo("Success", f"CSV file saved: {path}")

def csv_filtered_export():
    if 'filtered_data' not in globals():
        messagebox.showerror("Error", "Please filter data first!")
        return
    path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV-Dateien", "*.csv")])
    if path:
        generate_csv_filtered_file(path, filtered_data, data, None)
        messagebox.showinfo("Success", f"CSV file saved: {path}")

def generate_report():
    global data, stats, directory, file_name, filtered_data

    if data is None or stats is None:
        messagebox.showerror("Error", "Please load data and calculate statistics first.")
        return

    # Hier wird `selected_plots` aus den Checkbox-Variablen aktualisiert
    selected_plots = {
        "JV": jv_var.get(),
        "Box+Scatter": box_var.get(),
        "SeparateScan": separate_scan_var.get(), 
        "EQE": eqe_var.get(),
        "MPP": mpp_var.get(),
        "Table": table_var.get(), 
    }

    file_path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF files", "*.pdf")])
    if not file_path:
        return

    try:
        directory, file_name = generate_pdf_report(filtered_data, stats, selected_plots, file_path, nomad_url, token)
        messagebox.showinfo("Success", f"PDF report with filtered data saved to: {file_path}")
    except:
        try:
            directory, file_name = generate_pdf_report(data, stats, selected_plots, file_path, nomad_url, token)
            messagebox.showinfo("Success", f"PDF report with raw data saved to: {file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate report: {e}")


# Hauptfenster erstellen
root = tk.Tk()
root.title("Script for NOMAD data evaluation")
root.geometry("600x600")
#root.configure(bg="white")

# Checkbox-Variablen für Plots
jv_var = tk.BooleanVar(value=True)
box_var = tk.BooleanVar(value=True)
separate_scan_var = tk.BooleanVar(value=False)
eqe_var = tk.BooleanVar(value=False)
mpp_var = tk.BooleanVar(value=False)
table_var = tk.BooleanVar(value=True)

selected_plots = [
    ("JV Curves", jv_var),
    ("Box + Scatter Plots", box_var),
    ("Separate Backwards/Forwards", separate_scan_var),
    ("EQE Curves", eqe_var),
    ("MPP Curves", mpp_var),
    ("Data Table", table_var)
]

# Haupt-Frame mit Scroll-Funktion
main_frame = tk.Frame(root)
main_frame.pack(fill=tk.BOTH, expand=True)

canvas = tk.Canvas(main_frame)
scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=canvas.yview)
scrollable_frame = ttk.Frame(canvas)


scrollable_frame.bind(
    "<Configure>",
    lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
)

window_id = canvas.create_window((0, 0), window=scrollable_frame, anchor="center")

# Fensterbreite anpassen, wenn Größe geändert wird
def update_canvas_width(event):
    canvas.itemconfig(window_id, width=canvas.winfo_width())

canvas.bind("<Configure>", update_canvas_width)
canvas.configure(yscrollcommand=scrollbar.set)
canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

# Scrollen mit dem Mausrad aktivieren
def on_mouse_wheel(event):
    canvas.yview_scroll(-1 * (event.delta // 120), "units")

canvas.bind_all("<MouseWheel>", on_mouse_wheel)  # Für Windows

# **Hier wird sichergestellt, dass alle Elemente mittig ausgerichtet sind**
scrollable_frame.columnconfigure(0, weight=1)

# Widgets ins `scrollable_frame` einfügen
ttk.Label(scrollable_frame, text="NOMAD Login (name and password)", font=("Helvetica", 12, "bold")).grid(row=0, column=0, pady=5, sticky="n")

username_entry = ttk.Entry(scrollable_frame, width=30)
username_entry.grid(row=1, column=0, pady=5)
password_entry = ttk.Entry(scrollable_frame, width=30, show="*")
password_entry.grid(row=2, column=0, pady=5)
ttk.Button(scrollable_frame, text="Login", command=login_handler).grid(row=3, column=0, pady=5)

ttk.Button(scrollable_frame, text="Select File", command=select_file).grid(row=4, column=0, pady=5)
file_path_label = ttk.Label(scrollable_frame, text="Keine Datei ausgewählt", foreground="gray")
file_path_label.grid(row=5, column=0, pady=5)

ttk.Button(scrollable_frame, text="Load corresponding Data from NOMAD OASIS", command=load_data).grid(row=6, column=0, pady=10)
ttk.Button(scrollable_frame, text="filter your data", command=filter_data).grid(row=7, column=0, pady=10)
ttk.Button(scrollable_frame, text="Calculate Statistics", command=calculate_stats).grid(row=8, column=0, pady=10)
ttk.Button(scrollable_frame, text="generate csv (raw data)", command=csv_raw_export).grid(row=9, column=0, pady=10)
ttk.Button(scrollable_frame, text="Generate csv (filtered data)", command=csv_filtered_export).grid(row=10, column=0, pady=10)
ttk.Button(scrollable_frame, text="Generate Report", command=generate_report).grid(row=11, column=0, pady=10)

# Toggle-Funktion für Plot-Optionen
def toggle_plot_options():
    if plot_options_frame.winfo_ismapped():
        plot_options_frame.grid_remove()
        toggle_button.config(text="▶ Show Plot Options")
    else:
        plot_options_frame.grid(row=13, column=0, pady=5, sticky="n")
        toggle_button.config(text="▼ Hide Plot Options")

# Button für das Ein-/Ausklappen der Checkboxen
toggle_button = tk.Button(scrollable_frame, text="▶ Show Plot Options", command=toggle_plot_options)
toggle_button.grid(row=12, column=0, pady=10)

# Frame für die Checkboxen (zunächst versteckt)
plot_options_frame = tk.Frame(scrollable_frame)
plot_options_frame.grid(row=13, column=0, pady=5, sticky="n")
plot_options_frame.grid_remove()  # Startet versteckt

# Checkboxen erstellen
for idx, (text, var) in enumerate(selected_plots):
    tk.Checkbutton(plot_options_frame, text=text, variable=var).grid(row=idx, column=0, sticky="w", padx=10)

root.mainloop()
