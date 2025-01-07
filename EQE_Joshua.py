# -*- coding: utf-8 -*-
"""
Created on Tue Oct  1 17:20:23 2024

@author: mt1126
"""

import tkinter as tk
from tkinter import filedialog

import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import curve_fit 
import math
from scipy import constants as c

from matplotlib.cm import get_cmap

# Globale Variablen für den Speicherpfad, Dateinamen, x_min und x_max
Folder = ""
Filename = ""
x_min = 0
x_max = 0

class DynamicEntryApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Dynamische Pfad- und String-Eingabe")
        
        self.rows = []  # Liste für alle Elemente der dynamischen Zeilen

        # Erst die Speicherpfad und -namen Zeile hinzufügen
        self.create_fixed_row()

        # Erst die Buttons erstellen, dann die erste Zeile hinzufügen
        self.create_widgets()
        self.add_entry_row()  # Erst nach der Erstellung der Buttons

    def create_fixed_row(self):
        # Label für den Speicherpfad
        label_folder = tk.Label(self.root, text="Speicherpfad:")
        label_folder.grid(row=0, column=0, padx=10, pady=5)

        # Eingabefeld für den Speicherpfad
        self.entry_folder = tk.Entry(self.root, width=40)
        self.entry_folder.grid(row=0, column=1, padx=10, pady=5)

        # Durchsuchen Button für den Speicherpfad
        button_browse_folder = tk.Button(self.root, text="Durchsuchen", command=self.browse_folder)
        button_browse_folder.grid(row=0, column=2, padx=10, pady=5)

        # Label für den Dateinamen
        label_filename = tk.Label(self.root, text="Speichername:")
        label_filename.grid(row=0, column=3, padx=10, pady=5)

        # Eingabefeld für den Dateinamen
        self.entry_filename = tk.Entry(self.root, width=20)
        self.entry_filename.grid(row=0, column=4, padx=10, pady=5)

        # Label für x_min (nm)
        label_x_min = tk.Label(self.root, text="x_min [nm] (optiona input):")
        label_x_min.grid(row=1, column=0, padx=10, pady=5)

        # Eingabefeld für x_min (nm)
        self.entry_x_min = tk.Entry(self.root, width=20)
        self.entry_x_min.grid(row=1, column=1, padx=10, pady=5)

        # Label für x_max (nm)
        label_x_max = tk.Label(self.root, text="x_max [nm] (optional input):")
        label_x_max.grid(row=1, column=2, padx=10, pady=5)

        # Eingabefeld für x_max (nm)
        self.entry_x_max = tk.Entry(self.root, width=20)
        self.entry_x_max.grid(row=1, column=3, padx=10, pady=5)

    def create_widgets(self):
        # Button zum Hinzufügen einer neuen Zeile
        self.add_button = tk.Button(self.root, text="+", command=self.add_entry_row)
        self.add_button.grid(row=3, column=0, pady=10)

        # Button zum Entfernen der letzten Zeile
        self.remove_button = tk.Button(self.root, text="-", command=self.remove_entry_row)
        self.remove_button.grid(row=3, column=1, pady=10)

        # Submit-Button
        self.submit_button = tk.Button(self.root, text="Submit", command=self.submit_data)
        self.submit_button.grid(row=3, column=2, pady=10)

    def add_entry_row(self):
        row_index = len(self.rows) + 4  # Neue Zeile, basierend auf aktueller Anzahl der dynamischen Zeilen (Ab Row 4)

        # Pfad Label und Eingabefeld
        label_path = tk.Label(self.root, text=f"Pfad {row_index - 3}:")
        label_path.grid(row=row_index, column=0, padx=10, pady=5)

        entry_path = tk.Entry(self.root, width=40)
        entry_path.grid(row=row_index, column=1, padx=10, pady=5)

        # Durchsuchen Button
        button_browse = tk.Button(self.root, text="Durchsuchen", command=lambda e=entry_path: self.open_file_dialog(e))
        button_browse.grid(row=row_index, column=2, padx=10, pady=5)

        # String Eingabefeld
        entry_string = tk.Entry(self.root, width=20)
        entry_string.grid(row=row_index, column=3, padx=10, pady=5)

        # Speichere alle Widgets dieser Zeile in einer Liste
        self.rows.append({
            'label': label_path,
            'entry_path': entry_path,
            'button_browse': button_browse,
            'entry_string': entry_string
        })

        # Aktualisiere Buttons nach unten
        self.update_buttons_position()

        # Aktivere den "-" Button, wenn mehr als eine Zeile da ist
        self.remove_button.config(state=tk.NORMAL)

    def remove_entry_row(self):
        if len(self.rows) > 1:  # Überprüfe, ob mehr als eine Zeile vorhanden ist
            # Entferne die letzte Zeile (Label, Pfad, Button, String)
            last_row = self.rows.pop()  # Letzte Zeile aus der Liste entfernen
            
            # Entferne alle Widgets der letzten Zeile aus dem Grid und lösche sie
            last_row['label'].grid_forget()
            last_row['entry_path'].grid_forget()
            last_row['button_browse'].grid_forget()
            last_row['entry_string'].grid_forget()

            # Buttons-Position aktualisieren
            self.update_buttons_position()

        # Deaktiviere den "-" Button, wenn nur noch eine Zeile übrig ist
        if len(self.rows) == 1:
            self.remove_button.config(state=tk.DISABLED)

    def update_buttons_position(self):
        # Setze die Buttons (Hinzufügen, Entfernen, Submit) immer unter die letzte Zeile
        row_index = len(self.rows) + 4
        self.add_button.grid(row=row_index + 1, column=0, pady=10)
        self.remove_button.grid(row=row_index + 1, column=1, pady=10)
        self.submit_button.grid(row=row_index + 1, column=2, pady=10)

    def browse_folder(self):
        # Öffne den Datei-Dialog zum Auswählen eines Ordners
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

        # Speicherpfad und Dateinamen
        Folder = self.entry_folder.get()
        Filename = self.entry_filename.get()

        # x_min und x_max
        x_min = str(self.entry_x_min.get())
        x_max = str(self.entry_x_max.get())

        # Sammle die Daten der dynamischen Zeilen
        paths = [row['entry_path'].get() for row in self.rows]
        strings = [row['entry_string'].get() for row in self.rows]

        # Schließe das Fenster nach dem Absenden
        self.root.quit()
        self.root.destroy()

# Hauptprogramm
root = tk.Tk()
app = DynamicEntryApp(root)

# Deaktiviere den "-" Button, weil nur eine Zeile initial vorhanden ist
app.remove_button.config(state=tk.DISABLED)

root.mainloop()

file_paths = paths
anzahl_farben = len(file_paths)
dark_colors = [get_cmap("viridis")(i / anzahl_farben) for i in range(anzahl_farben)]
files = strings

def integriere_f_g(x_f, y_f, x_g, y_g): #integral selbst lösen

    y_f = np.array(y_f) / 100.0

    # Wellenlängenbereich der EQE bestimmen
    min_wavelength = max(min(x_f), min(x_g))
    max_wavelength = min(max(x_f), max(x_g))
    
    # Interpolation auf 1 nm Schritte
    wavelengths = np.arange(min_wavelength, max_wavelength + 1, 1)
    eqe_interp = np.interp(wavelengths, x_g, y_g)
    spectrum_interp = np.interp(wavelengths,x_f, y_f)
    
    # Umrechnung der Wellenlängen von nm in m
    wavelengths_m = wavelengths * 1e-9
       
    photon_flux = (spectrum_interp * wavelengths_m) / (c.h * c.c)  # Photonenfluss in 1/(m²·s·nm)
    jsc = np.sum(eqe_interp * photon_flux * (wavelengths[1] - wavelengths[0])) * c.e  # in A/m²
    
    # Umrechnung von A/m² in mA/cm²
    jsc_mA_cm2 = jsc * 1e3 / 1e4
    
    return round(jsc_mA_cm2,2)

def read_text_file(file_path = r"EQE_Sonnenspektrum_Joshua.txt"):
    x = []
    y = []
    with open(file_path, 'r') as file:
        next(file)
        
        for line in file:
            columns = line.split()
            
            x.append(float(columns[0]))
            y.append(float(columns[3]))
    return x,y

def read_data(file_path):
    data = []
    is_data_section = False
    with open(file_path, 'r') as file:
        for line in file:
            if "1	Integral" in line:
                try:
                    parts = line.split()
                    if len(parts) >= 3:
                        jsc.append(float(parts[2]))  # Third part as float
                except (ValueError, IndexError):
                    print(f"Error reading number after INTEGRALS: {line.strip()}")
            if is_data_section:
                values = line.split()
                if len(values) >= 2:
                    try:
                        data.append((float(values[0]), float(values[1])))
                    except ValueError:
                        continue
            elif "POINTS IN SPECTRUM END" in line:
                is_data_section = True
    return data

def gauss(x, a, x0, sigma):
    return a * np.exp(-(x - x0)**2 / (2 * sigma**2))

def find_gauss_minimum(x, y_arr):
    # Minimalen Wert und seinen Index finden
    y = y_arr.tolist()
    min_value = min(y)
    min_index = y.index(min_value)
    
    # Positive Werte links vom minimalen Wert finden
    left_index = None
    for i in range(min_index - 1, -1, -1):
        if y[i] >= 0:
            left_index = i
            break
    
    # Positive Werte rechts vom minimalen Wert finden
    right_index = None
    for i in range(min_index + 1, len(y)):
        if y[i] >= 0:
            right_index = i
            break
        
    #falls die messkurve etwas zu kurz ist setzt er hiermit den wert einfach auf max(x)
    if right_index == None:
        right_index = len(y)
        
    # Bereich der Daten zum Fitten auswählen
    fit_x = x[left_index:right_index+1]
    fit_y = y[left_index:right_index+1]
    
    # Gauss-Fit durchführen
    popt, _ = curve_fit(gauss, fit_x, fit_y, p0=[min_value, x[min_index], 10])
    
    # x-Wert des Minimums der Gauss-Funktion
    gauss_min_x = popt[1]
    
    # Plotten der Daten und des Fits
    plt.scatter(x, y, label='Data')
    plt.plot(fit_x, gauss(fit_x, *popt), 'r-', label='Gauss Fit')
    plt.title("Gaussian fit")
    #plt.title(file_paths[hilfe])
    plt.xlabel('wavelength [nm]')
    plt.ylabel('EQE derivative with Gaussian')
    plt.show()
    
    return gauss_min_x

def schneide_listen(x, y, x_min, x_max):
    x_min = int(x_min)
    x_max = int(x_max)
    try:
        # Indexe von x_min und x_max in der Liste x finden
        index_min = x.index(x_min)
    except ValueError:
        print(f"x_min ({x_min}) ist nicht in der Liste x vorhanden.")
        return None, None

    try:
        index_max = x.index(x_max)
    except ValueError:
        print(f"x_max ({x_max}) ist nicht in der Liste x vorhanden.")
        return None, None

    # Die Listen x und y basierend auf den gefundenen Indexen abschneiden
    x_abgeschnitten = x[index_min:index_max+1]
    y_abgeschnitten = y[index_min:index_max+1]

    return x_abgeschnitten, y_abgeschnitten

def plot_multiple_files(file_paths): 
    a,b = read_text_file()
    max_value_y = 0
    find_inflection_point(file_paths)
    plt.figure(figsize=(14, 6))
    i = 0 
    for file_path in file_paths:
        data = read_data(file_path)
        if data:
            x_values, y_values = zip(*data)
            if x_min != "" and x_max != "":
                x_values, y_values = schneide_listen(x_values, y_values, x_min, x_max)
            if max_value_y < max(y_values):
                max_value_y = max(y_values)
            print("Jsc berechnet: ", integriere_f_g(a,b,x_values,y_values), " in mA/cm^2")
            plt.plot(x_values, y_values, linewidth = 3, color = dark_colors[i], label=files[i]+"\n"+"Jsc: "+ str(round(jsc[i],2)) + " mA/cm$^2$" +"\n"+"band gap: "+str(round(float(1240/bandluecken[i]),2)) + " eV")
            i += 1
        else:
            print(f"No numerical data found in {file_path}.")
    
    plt.xlabel('wavelength [nm]', fontsize = 17)
    plt.ylabel('EQE [%]', fontsize = 17)
    plt.xticks(fontsize = 17)
    yticks = [i for i in range(0,math.ceil(max_value_y/10)*10+10,10)] #erstellt eine liste von 0 bis max EQE bis auf 10 aufgerundet in 10er schritten
    plt.yticks(yticks, fontsize = 17)
    plt.ylim(0)
    plt.legend(fontsize = 13, loc='center left', bbox_to_anchor=(1, 0.5))
    plt.tight_layout(rect=[0, 0, 0.85, 1])
    plt.savefig(Folder+"/" + Filename + ".png", dpi = 1000, bbox_inches='tight')
    
    return

#habs mal über die nullstelle der zweiten abl gemacht aber minimum der ersten abl ist was einfacher
def find_inflection_point(file_paths):
    plt.figure(figsize=(10, 6))
    i = 0
    for file_path in file_paths:
        data = read_data(file_path)
        if data:
            x_values, y_values = zip(*data)
            zweite_abl = np.gradient(y_values, x_values)
            plt.plot(x_values, zweite_abl, label=files[i])
            plt.xlabel('wavelength [nm]')
            plt.ylabel('first derivation')
            plt.title('1st derivate')
            plt.legend()
            plt.show()
            i += 1
            bandluecken.append(find_gauss_minimum(x_values, zweite_abl))
        else:
            print(f"No numerical data found in {file_path}.")
    return 

global bandluecken #band gaps
bandluecken = []
global jsc
jsc = []

#call function
plot_multiple_files(file_paths)
