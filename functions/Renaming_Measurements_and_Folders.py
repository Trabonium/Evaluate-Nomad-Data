import os
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox
import re
import datetime

def Renaming_folders(master):

    def extract_x_y(filename):
        pattern = r"_([0-9]{2})_Cycle_([0-9]+)_illu\.csv$"
        match = re.search(pattern, filename)
        if match:
            x = match.group(1)
            y = match.group(2)
            return int(x), int(y)
        return None

    def get_oldest_file_date(folder_path: str) -> str:
        try:
            files = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
            if not files:
                return "No files found"
            
            oldest_file = min(files, key=os.path.getmtime)  # Statt getctime jetzt getmtime
            oldest_date = datetime.datetime.fromtimestamp(os.path.getmtime(oldest_file))  # Korrekte Umwandlung
            return oldest_date.strftime("%Y%m%d")
        except Exception:
            return "Error"

    def select_path():
        path = filedialog.askdirectory()
        path_entry.delete(0, tk.END)
        path_entry.insert(0, path)
        if toggle_var.get():
            auto_date = get_oldest_file_date(path)
            datum_entry.config(state=tk.NORMAL)
            datum_entry.delete(0, tk.END)
            datum_entry.insert(0, auto_date if auto_date != "Error" else "")
            datum_entry.config(state=tk.DISABLED)

    def toggle_date():
        if toggle_var.get():
            datum_entry.config(state=tk.NORMAL)
            auto_date = get_oldest_file_date(path_entry.get())
            datum_entry.delete(0, tk.END)
            datum_entry.insert(0, auto_date if auto_date != "Error" else "")
            datum_entry.config(state=tk.DISABLED)
        else:
            datum_entry.config(state=tk.NORMAL)
            datum_entry.delete(0, tk.END)

    def get_unique_folder_name(base_path):
        counter = 1
        new_folder_path = base_path + "_ELN"
        while os.path.exists(new_folder_path):
            new_folder_path = base_path + f"_ELN{counter}"
            counter += 1
        return new_folder_path

    def submit():
        original_path = path_entry.get()
        kuerzel = kuerzel_entry.get()
        datum = datum_entry.get()
        prozessart = prozessart_entry.get()

        new_folder_path = get_unique_folder_name(os.path.join(os.path.dirname(original_path), os.path.basename(original_path)))

        shutil.copytree(original_path, new_folder_path)
        i = 0
        kopie = None
        cut = 0

        for pfad, dirs, files in os.walk(new_folder_path):
            for file in files:
                old_file_path = os.path.join(pfad, file)
                stringabfrage = extract_x_y(file)
                if kopie and kopie[:-cut] != file[:-cut] and file[:-cut] != "":
                    i += 1
                kopie = file
                if stringabfrage:
                    pixel, cycle_measurement = stringabfrage
                    cut = 20 if len(file) > 20 else 4
                    new_file_name = f"KIT_{kuerzel}_{datum}_{file[:-cut].replace('_','-')}_0_{i}.px{pixel}Cycle_{cycle_measurement}.{prozessart}.{file[-3:]}"
                else:
                    cut = 4
                    new_file_name = f"KIT_{kuerzel}_{datum}_{file[:-4].replace('_','-')}_0_{i}.px0Cycle_0.{prozessart}.{file[-3:]}"

                new_file_path = os.path.join(pfad, new_file_name)
                os.rename(old_file_path, new_file_path)

        messagebox.showinfo("Copy Successful", f"New Folder at {pfad}")

    # Erstelle ein Toplevel-Fenster anstatt eines neuen Tk-Fensters
    rename_window = tk.Toplevel(master)
    rename_window.title("ELN Name Converter")

    tk.Label(rename_window, text="Folder path:").grid(row=0, column=0, padx=10, pady=10)
    path_entry = tk.Entry(rename_window, width=50)
    path_entry.grid(row=0, column=1, padx=10, pady=10)
    tk.Button(rename_window, text="Choose Path", command=select_path).grid(row=0, column=2, padx=10, pady=10)

    tk.Label(rename_window, text="Your name (RaPe, DaBa, ThFe, ...):").grid(row=1, column=0, padx=10, pady=10)
    kuerzel_entry = tk.Entry(rename_window, width=50)
    kuerzel_entry.grid(row=1, column=1, padx=10, pady=10)

    tk.Label(rename_window, text="Date (YYYYMMDD):").grid(row=2, column=0, padx=10, pady=10)
    datum_entry = tk.Entry(rename_window, width=40)
    datum_entry.grid(row=2, column=1, padx=10, pady=10)

    toggle_var = tk.BooleanVar()
    toggle_button = tk.Checkbutton(rename_window, text="Use oldest file date", variable=toggle_var, command=toggle_date)
    toggle_button.grid(row=2, column=2, padx=10, pady=10)

    tk.Label(rename_window, text="Process (jv, eqe, ...):").grid(row=3, column=0, padx=10, pady=10)
    prozessart_entry = tk.Entry(rename_window, width=50)
    prozessart_entry.grid(row=3, column=1, padx=10, pady=10)

    tk.Button(rename_window, text="Submit", command=submit).grid(row=4, columnspan=3, pady=20)

    rename_window.grab_set()  # Blockiert andere Fenster bis zum Schließen
    rename_window.wait_window()
    return
