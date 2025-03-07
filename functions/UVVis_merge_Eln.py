import tkinter as tk
from tkinter import filedialog, messagebox
import pandas as pd
import os

def UVVis_merge(master):
    """Erzeugt ein Toplevel-Fenster für das Zusammenführen von Dateien."""

    def get_unique_filename(original_path, new_filename):
        dir_path = os.path.dirname(original_path)
        new_path = os.path.join(dir_path, new_filename + ".csv")
        counter = 1
        while os.path.exists(new_path):
            new_path = os.path.join(dir_path, f"{new_filename}_{counter}.csv")
            counter += 1
        return new_path

    def merge(reflection_file, transmission_file, result_file):
        if reflection_file.endswith(".csv"):  # UVVis im 2. OG
            df_R = pd.read_csv(reflection_file, sep=",", header=0, names=["Wellenlaenge_R", "Reflection"])
            df_T = pd.read_csv(transmission_file, sep=",", header=0, names=["Wellenlaenge_T", "Transmission"])
        elif reflection_file.endswith(".dat"):  # UVVis im TFL
            df_R = pd.read_csv(reflection_file, sep=r'\s+', header=None, names=["Wellenlaenge_R", "Reflection"])
            df_T = pd.read_csv(transmission_file, sep=r'\s+', header=None, names=["Wellenlaenge_T", "Transmission"])

        min_wavelength = max(df_R["Wellenlaenge_R"].min(), df_T["Wellenlaenge_T"].min())
        max_wavelength = min(df_R["Wellenlaenge_R"].max(), df_T["Wellenlaenge_T"].max())

        df_R = df_R[(df_R["Wellenlaenge_R"] >= min_wavelength) & (df_R["Wellenlaenge_R"] <= max_wavelength)]
        df_T = df_T[(df_T["Wellenlaenge_T"] >= min_wavelength) & (df_T["Wellenlaenge_T"] <= max_wavelength)]

        common_x = df_R["Wellenlaenge_R"].tolist()
        y1 = df_R["Reflection"].tolist()
        y2 = df_T["Transmission"].tolist()

        if reflection_file.endswith(".dat"):  # Sicherstellen, dass die Wellenlängen aufsteigend sind
            common_x.reverse()
            y1.reverse()
            y2.reverse()

        df = pd.DataFrame({"wavelength": common_x, "Reflection": y1, "Transmission": y2})
        speicherpfad = get_unique_filename(reflection_file, result_file)
        df.to_csv(speicherpfad, index=False, sep=";")
        messagebox.showinfo("Success", "Files merged successfully!")

    def select_file(entry):
        filepath = filedialog.askopenfilename(filetypes=[("CSV and DAT files", "*.csv;*.dat")])
        if filepath:
            entry.delete(0, tk.END)
            entry.insert(0, filepath)
        update_result()

    def update_result(*args):
        result.set(f"KIT_{entry_name.get()}_{entry_date.get()}_{entry_freetext.get()}_{entry_batch.get()}_{entry_subbatch.get()}")

    def save_action():
        if entry_reflection.get()[-4:] != entry_transmission.get()[-4:]:
            messagebox.showerror("Error", "Reflection & transmission need to be in the same format!")
        else:
            merge(entry_reflection.get(), entry_transmission.get(), result.get())

    # Toplevel-Fenster erstellen
    merge_window = tk.Toplevel(master)
    merge_window.title("Script to merge transmission and reflection data")

    # UI-Elemente hinzufügen (wie in der Originalversion)
    label_reflection = tk.Label(merge_window, text="Reflexion:")
    label_reflection.grid(row=0, column=0, padx=5, pady=5)
    entry_reflection = tk.Entry(merge_window, width=50)
    entry_reflection.grid(row=0, column=1, padx=5, pady=5)
    button_reflection = tk.Button(merge_window, text="Search", command=lambda: select_file(entry_reflection))
    button_reflection.grid(row=0, column=2, padx=5, pady=5)

    label_transmission = tk.Label(merge_window, text="Transmission:")
    label_transmission.grid(row=1, column=0, padx=5, pady=5)
    entry_transmission = tk.Entry(merge_window, width=50)
    entry_transmission.grid(row=1, column=1, padx=5, pady=5)
    button_transmission = tk.Button(merge_window, text="Search", command=lambda: select_file(entry_transmission))
    button_transmission.grid(row=1, column=2, padx=5, pady=5)

    # Texteingaben
    entry_name = tk.StringVar()
    entry_date = tk.StringVar()
    entry_freetext = tk.StringVar()
    entry_batch = tk.StringVar()
    entry_subbatch = tk.StringVar()

    entry_name.trace_add("write", update_result)
    entry_date.trace_add("write", update_result)
    entry_freetext.trace_add("write", update_result)
    entry_batch.trace_add("write", update_result)
    entry_subbatch.trace_add("write", update_result)

    fields = [("Name:", entry_name), ("Date:", entry_date), ("Free Text:", entry_freetext), ("Batch:", entry_batch), ("Subbatch:", entry_subbatch)]
    for i, (label, var) in enumerate(fields, start=2):
        tk.Label(merge_window, text=label).grid(row=i, column=0, padx=5, pady=5)
        tk.Entry(merge_window, textvariable=var, width=50).grid(row=i, column=1, padx=5, pady=5)


    # Dynamische Ergebnisanzeige
    result = tk.StringVar()
    label_result = tk.Label(merge_window, textvariable=result, fg="blue")
    label_result.grid(row=len(fields) + 2, column=0, columnspan=3, padx=5, pady=10)

    # Save Button
    button_save = tk.Button(merge_window, text="Save", command=save_action)
    button_save.grid(row=len(fields)+3, column=0, columnspan=3, padx=5, pady=10)

    merge_window.grab_set()  # Toplevel blockiert andere Fenster bis zum Schließen
    merge_window.wait_window()
    return
