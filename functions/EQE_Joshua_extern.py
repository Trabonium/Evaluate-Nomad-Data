import tkinter as tk
from tkinter import filedialog
import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import curve_fit
import math
from scipy import constants as c
import matplotlib as cmaps

# Globale Variablen für den Speicherpfad, Dateinamen, x_min und x_max
Folder = ""
Filename = ""
x_min = 0
x_max = 0

class DynamicEntryApp(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("EQE plotting")
        
        self.rows = []  # Liste für alle Elemente der dynamischen Zeilen

        # Sperrt die Interaktion mit dem Hauptfenster
        self.grab_set()

        # Erst die Speicherpfad und -namen Zeile hinzufügen
        self.create_fixed_row()

        # Erst die Buttons erstellen, dann die erste Zeile hinzufügen
        self.create_widgets()
        self.add_entry_row()  # Erst nach der Erstellung der Buttons

    def create_fixed_row(self):
        label_folder = tk.Label(self, text="Path to save:")
        label_folder.grid(row=0, column=0, padx=10, pady=5)

        self.entry_folder = tk.Entry(self, width=40)
        self.entry_folder.grid(row=0, column=1, padx=10, pady=5)

        button_browse_folder = tk.Button(self, text="Search", command=self.browse_folder)
        button_browse_folder.grid(row=0, column=2, padx=10, pady=5)

        label_filename = tk.Label(self, text="Name to save:")
        label_filename.grid(row=0, column=3, padx=10, pady=5)

        self.entry_filename = tk.Entry(self, width=20)
        self.entry_filename.grid(row=0, column=4, padx=10, pady=5)

        label_x_min = tk.Label(self, text="x_min [nm] (optional input):")
        label_x_min.grid(row=1, column=0, padx=10, pady=5)

        self.entry_x_min = tk.Entry(self, width=20)
        self.entry_x_min.grid(row=1, column=1, padx=10, pady=5)

        label_x_max = tk.Label(self, text="x_max [nm] (optional input):")
        label_x_max.grid(row=1, column=2, padx=10, pady=5)

        self.entry_x_max = tk.Entry(self, width=20)
        self.entry_x_max.grid(row=1, column=3, padx=10, pady=5)

    def create_widgets(self):
        self.add_button = tk.Button(self, text="+", command=self.add_entry_row)
        self.add_button.grid(row=3, column=0, pady=10)

        self.remove_button = tk.Button(self, text="-", command=self.remove_entry_row)
        self.remove_button.grid(row=3, column=1, pady=10)

        self.submit_button = tk.Button(self, text="Submit", command=self.submit_data)
        self.submit_button.grid(row=3, column=2, pady=10)

    def add_entry_row(self):
        row_index = len(self.rows) + 4  # Neue Zeile ab Row 4

        label_path = tk.Label(self, text=f"Path {row_index - 3}:")
        label_path.grid(row=row_index, column=0, padx=10, pady=5)

        entry_path = tk.Entry(self, width=40)
        entry_path.grid(row=row_index, column=1, padx=10, pady=5)

        button_browse = tk.Button(self, text="Search", command=lambda e=entry_path: self.open_file_dialog(e))
        button_browse.grid(row=row_index, column=2, padx=10, pady=5)

        entry_string = tk.Entry(self, width=20)
        entry_string.grid(row=row_index, column=3, padx=10, pady=5)

        self.rows.append({'label': label_path, 'entry_path': entry_path, 'button_browse': button_browse, 'entry_string': entry_string})

        self.update_buttons_position()
        self.remove_button.config(state=tk.NORMAL)

    def remove_entry_row(self):
        if len(self.rows) > 1:
            last_row = self.rows.pop()
            last_row['label'].grid_forget()
            last_row['entry_path'].grid_forget()
            last_row['button_browse'].grid_forget()
            last_row['entry_string'].grid_forget()
            self.update_buttons_position()

        if len(self.rows) == 1:
            self.remove_button.config(state=tk.DISABLED)

    def update_buttons_position(self):
        row_index = len(self.rows) + 4
        self.add_button.grid(row=row_index + 1, column=0, pady=10)
        self.remove_button.grid(row=row_index + 1, column=1, pady=10)
        self.submit_button.grid(row=row_index + 1, column=2, pady=10)

    def browse_folder(self):
        folder_path = filedialog.askdirectory()
        if folder_path:
            self.entry_folder.delete(0, tk.END)
            self.entry_folder.insert(0, folder_path)

    def open_file_dialog(self, entry):
        file_path = filedialog.askopenfilename(filetypes=[("DAT files", "*.dat")])
        if file_path:
            entry.delete(0, tk.END)
            entry.insert(0, file_path)

    def submit_data(self):
        global Folder, Filename, x_min, x_max, paths, strings

        Folder = self.entry_folder.get()
        Filename = self.entry_filename.get()
        x_min = str(self.entry_x_min.get())
        x_max = str(self.entry_x_max.get())

        paths = [row['entry_path'].get() for row in self.rows]
        strings = [row['entry_string'].get() for row in self.rows]

        self.destroy()  # Fenster schließen


def GUI_fuer_Joshuas_EQE(master):
    eqe_gui = DynamicEntryApp(master)
    master.wait_window(eqe_gui)  # Wartet, bis das Fenster geschlossen wird
