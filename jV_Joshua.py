import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import csv
import sys
import re

# Option für maximale Zeilen
pd.set_option('display.max_rows', None)

# Option für maximale Spalten
pd.set_option('display.max_columns', None)

# Option für die maximale Breite des Outputs
pd.set_option('display.width', None)

# Optional: um den Inhalt der Spalten vollständig anzuzeigen
pd.set_option('display.max_colwidth', None)

# Globale Variablen
global_boolean = True
global_boolean2 = True
global_boolean3 = True
global_boolean4 = True
global_boolean5 = False
global_string_lists = []
global_name_lists = []
global_min_values = []
global_max_values = []
global_cycle_value = 0  # Globale Variable für den Cycle-Wert

#schranken zum daten ausschließen
default_max_values = []
default_min_values = []

for i in range(10):
    default_max_values.append(np.inf)
    default_min_values.append(-np.inf)
    

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Speicherpfad und Eingaben")
        
        # Setzt die Fenstergröße auf 800x400 Pixel
        self.root.geometry("830x400")

        # Initialisierung der Listen für Eingabefelder und Labels
        self.entry_rows = []
        self.name_rows = []
        self.labels = []
        self.min_entries = []
        self.max_entries = []

        # Speicherpfad und -name
        self.path_label = tk.Label(root, text="data path:")
        self.path_label.grid(row=0, column=0, padx=5, pady=5)

        self.path_entry = tk.Entry(root, width=50)
        self.path_entry.grid(row=0, column=1, padx=5, pady=5)

        self.browse_button = tk.Button(root, text="search", command=self.browse)
        self.browse_button.grid(row=0, column=2, padx=5, pady=5)

        self.name_label = tk.Label(root, text="name to save:")
        self.name_label.grid(row=1, column=0, padx=5, pady=5)

        self.name_entry = tk.Entry(root, width=50)
        self.name_entry.grid(row=1, column=1, padx=5, pady=5)

        # Eingabefeld für "Cycle"
        self.cycle_label = tk.Label(root, text="Cycle:")
        self.cycle_label.grid(row=1, column=2, padx=5, pady=5)

        self.cycle_value = tk.StringVar()
        self.cycle_value.set("0")  # Standardwert ist 0

        vcmd = (self.root.register(self.validate_cycle), '%P')  # Validierungsfunktion für Cycle

        self.cycle_entry = tk.Entry(root, textvariable=self.cycle_value, validate="key", validatecommand=vcmd, width=10)
        self.cycle_entry.grid(row=1, column=3, padx=5, pady=5)

        # Überschriften für Min- und Max-Werte
        self.min_label = tk.Label(root, text="Min Values")
        self.min_label.grid(row=0, column=4, padx=5, pady=5)

        self.max_label = tk.Label(root, text="Max Values")
        self.max_label.grid(row=0, column=5, padx=5, pady=5)

        # Plus und Minus Buttons initialisieren
        self.add_button = tk.Button(root, text="+", command=self.add_entry_row)
        self.remove_button = tk.Button(root, text="-", command=self.remove_entry_row)

        # "Fertig" Button
        self.finish_button = tk.Button(root, text="done", bg="blueviolet", command=self.finish)
        
        #abbrechenbutton
        self.abort_button = tk.Button(root, text="abort", bg='red', command=self.abort)

        # Toggle Button (Boolean Button)
        self.boolean_button_label = tk.Label(root, text="points in boxplot?")
        self.boolean_button_label.grid(row=8, column=4, padx=5, pady=5)
        self.boolean_button = tk.Button(root, text="active", bg="green", command=self.toggle_boolean)
        self.boolean_button.grid(row=8, column=5, padx=5, pady=5)
        
        # Toggle Button2 (Boolean Button)
        self.boolean_button2_label = tk.Label(root, text="best JV plot?")
        self.boolean_button2_label.grid(row=9, column=4, padx=5, pady=5)
        self.boolean_button2 = tk.Button(root, text="active", bg="green", command=self.toggle_boolean2)
        self.boolean_button2.grid(row=9, column=5, padx=5, pady=5)
        
        # Toggle Button3 (Boolean Button)
        self.boolean_button3_label = tk.Label(root, text="median JV plot?")
        self.boolean_button3_label.grid(row=10, column=4, padx=5, pady=5)
        self.boolean_button3 = tk.Button(root, text="active", bg="green", command=self.toggle_boolean3)
        self.boolean_button3.grid(row=10, column=5, padx=5, pady=5)
        
        # Toggle Button3 (Boolean Button)
        self.boolean_button4_label = tk.Label(root, text="invert JV plot?")
        self.boolean_button4_label.grid(row=11, column=4, padx=5, pady=5)
        self.boolean_button4 = tk.Button(root, text="active", bg="green", command=self.toggle_boolean4)
        self.boolean_button4.grid(row=11, column=5, padx=5, pady=5)
        
        # Toggle Button3 (Boolean Button)
        self.boolean_button5_label = tk.Label(root, text="Hysteresis plot?")
        self.boolean_button5_label.grid(row=11, column=4, padx=5, pady=5)
        self.boolean_button5 = tk.Button(root, text="inactive", bg="red", command=self.toggle_boolean5)
        self.boolean_button5.grid(row=11, column=5, padx=5, pady=5)
        
        # "Variation 1" hinzufügen, als Minimum
        self.add_entry_row()

        # Min und Max Felder für die verschiedenen Werte einfügen
        self.create_min_max_rows()

        # Standardwerte in die Min- und Max-Entry-Felder einfügen
        self.set_default_min_max_values()
        
    def toggle_boolean(self):
        """Schaltet den globalen Boolean-Wert um und passt die Farbe des Buttons an"""
        global global_boolean
        global_boolean = not global_boolean
        if global_boolean:
            self.boolean_button.config(text="active", bg="green")
        else:
            self.boolean_button.config(text="inactive", bg="red")
            
    def toggle_boolean2(self):
        """Schaltet den globalen Boolean-Wert um und passt die Farbe des Buttons an"""
        global global_boolean2
        global_boolean2 = not global_boolean2
        if global_boolean2:
            self.boolean_button2.config(text="active", bg="green")
        else:
            self.boolean_button2.config(text="inactive", bg="red")
            
    def toggle_boolean3(self):
        """Schaltet den globalen Boolean-Wert um und passt die Farbe des Buttons an"""
        global global_boolean3
        global_boolean3 = not global_boolean3
        if global_boolean3:
            self.boolean_button3.config(text="active", bg="green")
        else:
            self.boolean_button3.config(text="inactive", bg="red")
            
    def toggle_boolean4(self):
        """Schaltet den globalen Boolean-Wert um und passt die Farbe des Buttons an"""
        global global_boolean4
        global_boolean4 = not global_boolean4
        if global_boolean4:
            self.boolean_button4.config(text="active", bg="green")
        else:
            self.boolean_button4.config(text="inactive", bg="red")
    
    def toggle_boolean5(self):
        """Schaltet den globalen Boolean-Wert um und passt die Farbe des Buttons an"""
        global global_boolean5
        global_boolean5 = not global_boolean5
        if global_boolean5:
            self.boolean_button5.config(text="active", bg="green")
        else:
            self.boolean_button5.config(text="inactive", bg="red")
        
    def browse(self):
        path = filedialog.askdirectory()
        self.path_entry.delete(0, tk.END)
        self.path_entry.insert(0, path)

    def add_entry_row(self):
        # Label für "Variation X"
        variation_label = tk.Label(self.root, text=f"Variation {len(self.entry_rows) + 1}:")
        variation_label.grid(row=len(self.entry_rows) + 2, column=0, padx=5, pady=5)

        # Eingabefeld für Strings (Variationen)
        entry = tk.Entry(self.root, width=50)
        entry.grid(row=len(self.entry_rows) + 2, column=1, padx=5, pady=5)

        # Eingabefeld für Namen
        name_entry = tk.Entry(self.root, width=20)
        name_entry.grid(row=len(self.entry_rows) + 2, column=2, padx=5, pady=5)

        # Speichern von Label, Entry für Variationen und Namen
        self.labels.append(variation_label)
        self.entry_rows.append(entry)
        self.name_rows.append(name_entry)

        # Fenstergröße automatisch anpassen und Buttons neu positionieren
        self.adjust_window_size(expand=True)
        self.update_button_position()

    def remove_entry_row(self):
        if len(self.entry_rows) > 1:  # Nur entfernen, wenn mehr als 1 Zeile vorhanden ist
            # Entferne das letzte Eingabefeld und Label
            entry = self.entry_rows.pop()
            entry.grid_forget()

            name_entry = self.name_rows.pop()
            name_entry.grid_forget()

            label = self.labels.pop()
            label.grid_forget()

            # Fenstergröße verringern und Buttons neu positionieren
            self.adjust_window_size(expand=False)
            self.update_button_position()

    def adjust_window_size(self, expand=True):
        """Passt die Fenstergröße an den aktuellen Inhalt an.
        Bei `expand=True` wird die Höhe vergrößert, bei `expand=False` wird die Höhe verkleinert."""
        self.root.update_idletasks()  # Aktualisiert die Layoutänderungen
        width = self.root.winfo_width()  # Aktuelle Fensterbreite beibehalten
        
        # Fensterhöhe um 30 Pixel vergrößern oder verkleinern
        if expand:
            height = self.root.winfo_height() + 30
        else:
            height = self.root.winfo_height() - 30
        
        self.root.geometry(f"{width}x{height}")

    def update_button_position(self):
        """Positioniert die Buttons unter der letzten Eingabezeile"""
        row_position = len(self.entry_rows) + 2  # +2, weil wir bei Zeile 0 und 1 oben anfangen
        self.add_button.grid(row=row_position, column=0, padx=5, pady=5)
        self.remove_button.grid(row=row_position, column=1, padx=5, pady=5)
        self.finish_button.grid(row=row_position, column=2, padx=5, pady=5)
        self.abort_button.grid(row=row_position+1, column=2, padx=5, pady=5)
        
    def create_min_max_rows(self):
        """Erstellt die Eingabefelder für Min- und Max-Werte"""
        labels = ["PCE", "FF", "Jsc", "Voc", "Hysteresis Index"]
        
        for i, label_text in enumerate(labels):
            # Labels für die Werte
            value_label = tk.Label(self.root, text=label_text)
            value_label.grid(row=i + 2, column=3, padx=5, pady=5)

            # Min- und Max-Eingabefelder
            min_entry = tk.Entry(self.root, width=10)
            min_entry.grid(row=i + 2, column=4, padx=5, pady=5)

            max_entry = tk.Entry(self.root, width=10)
            max_entry.grid(row=i + 2, column=5, padx=5, pady=5)

            # Eingabefelder speichern
            self.min_entries.append(min_entry)
            self.max_entries.append(max_entry)

    def set_default_min_max_values(self):
        """Setzt die Standardwerte in die Min- und Max-Entry-Felder"""
        for i in range(len(default_min_values) // 2):  # Nur jede zweite Zahl anzeigen
            # Überprüfe, ob die Min- und Max-Listen korrekt gefüllt sind
            if i < len(self.min_entries) and i < len(self.max_entries):
                # Setzt nur jede zweite Zahl für die Anzeige
                self.min_entries[i].insert(0, str(default_min_values[i * 2]))
                self.max_entries[i].insert(0, str(default_max_values[i * 2]))

    def validate_cycle(self, value_if_allowed):
        """Stellt sicher, dass nur natürliche Zahlen zwischen 0 und 10 eingegeben werden können"""
        if value_if_allowed.isdigit():
            value = int(value_if_allowed)
            return 0 <= value <= 10
        return False

    def get_min_max_values(self):
        """Erfasst die Min- und Max-Werte aus den Eingabefeldern"""
        self.min_values = []
        self.max_values = []

        for i in range(len(self.min_entries)):
            min_value = self.min_entries[i].get()
            max_value = self.max_entries[i].get()

            # Standardwerte verwenden, wenn die Felder leer sind
            if not min_value:
                min_value = default_min_values[i * 2]
            if not max_value:
                max_value = default_max_values[i * 2]

            self.min_values.extend([float(min_value), float(min_value)])  # Zweimal einfügen
            self.max_values.extend([float(max_value), float(max_value)])  # Zweimal einfügen
            
    def string_to_list(self, input_string):
        
        input_string = input_string.replace(" ", "")
        parts = input_string.split(',')

        result = []

        for part in parts:
            if '-' in part:  # Bereichsanalyse, z.B. "A1-A4"
                start, end = part.split('-')

                # Validierung: Der Buchstabe muss übereinstimmen
                if start[0] != end[0]:
                    raise ValueError(f"Ungültiger Bereich: {start}-{end} (Buchstaben stimmen nicht überein)")

                # Extrahiere den Buchstaben und die Zahlen
                letter = start[0]
                start_num = int(start[1:])
                end_num = int(end[1:])

                # Generiere den Bereich und füge ihn zur Ergebnisliste hinzu
                result.extend([f"{letter}{num}" for num in range(start_num, end_num + 1)])
            else:
                # Einzelne Werte, z.B. "A7"
                result.append(part)

        return result

    def get_string_lists(self):
        """Erfasst die Variationen und Namen und zeigt Fehler in einem Dialog an."""
        self.string_lists = []
        self.name_lists = []

        for entry, name_entry in zip(self.entry_rows, self.name_rows):
            # Variationen
            input_value = entry.get()  # Das ist der Input mit den Kommas
            try:
                cleaned_input = self.string_to_list(input_value)
                self.string_lists.append(cleaned_input)
            except ValueError as e:
                # Fehlerdialog anzeigen
                messagebox.showerror("Eingabefehler", f"Fehler bei der Verarbeitung der Eingabe: {e}")
                return  # Beende die Verarbeitung und warte auf Korrektur durch den Benutzer

            # Namen
            name_value = name_entry.get()
            if name_value:
                self.name_lists.append([name_value])
                
    def abort(self):
        self.root.destroy()
        sys.exit()
    
    def finish(self):
        """Schließt das Fenster und zeigt die Daten an."""
        self.get_string_lists()  # Erfasst die Eingaben

        # Nur fortfahren, wenn keine Fehler aufgetreten sind
        if not self.string_lists:
            return

        self.get_min_max_values()  # Erfasst die Min/Max-Werte

        global global_string_lists, global_name_lists, global_min_values, global_max_values, global_cycle_value, path_entry, name_entry

        # Werte in die globalen Variablen speichern
        helplist = self.string_lists
        global_string_lists = [[element + '_' for element in unterliste] for unterliste in helplist]
        global_name_lists = self.name_lists
        global_min_values = self.min_values
        global_max_values = self.max_values
        global_cycle_value = int(self.cycle_value.get())  # Cycle-Wert speichern
        path_entry = self.path_entry.get()
        name_entry = self.name_entry.get()

        # Fenster schließen
        self.root.destroy()  # Schließt das Fenster vollständig

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
    
###         VIELE JVs auslesen

def Datenauslesen():
    epsilon = 1e-9
    
    name = []
    PSC_f = []
    PSC_b = []
    FF_f = []
    FF_b = []
    Jsc_f = []
    Jsc_b = []
    Voc_f = []
    Voc_b = []
    hysteresis_index = []
    
    Scan_Folder = path_entry
    namen = name_entry + "_data_collection"+".csv"
    ablage = Scan_Folder+"/"+namen
    if os.path.exists(ablage):
        os.remove(ablage)
    files = os.listdir(Scan_Folder)
    csv_files = list(filter(lambda x: x.endswith('illu.csv') and "Cycle_"+str(global_cycle_value) in x and "MPP" not in x and "mpp" not in x and "Mpp" not in x, files))
    csv_files.sort(key=lambda x: os.path.getmtime(Scan_Folder+'/'+x))
    
    for i in (range(len(csv_files))):
        with open(Scan_Folder+"/"+csv_files[i], 'r', encoding='latin1') as file:
            lines = file.readlines()
            line_6 = lines[5]
            line_7 = lines[6]
            line_8 = lines[7]
            line_9 = lines[8]  # Index 8 entspricht der 9. Zeile (0-basiert)
        try:
            Jsc = line_6.split()
            Voc = line_7.split()
            FF = line_8.split()
            eff = line_9.split() 
            name.append(csv_files[i])
            PSC_f.append(float(eff[1]))
            PSC_b.append(float(eff[2]))
            FF_f.append(float(FF[2]))
            FF_b.append(float(FF[3]))
            Jsc_f.append(float(Jsc[2]))
            Jsc_b.append(float(Jsc[3]))
            Voc_f.append(float(Voc[2]))
            Voc_b.append(float(Voc[3]))
            if abs(float(eff[2])) < epsilon:
                hysteresis_index.append(0)
            else:
                hysteresis_index.append((float(eff[2])-float(eff[1]))/float(eff[2]))
        except:
            print("data reading broke :(")
        
    dict = {"filename": name, 'PSC_reverse': PSC_f, 'PSC_forwards': PSC_b, 'FF_reverse': FF_f, 'FF_forwards': FF_b, 'Jsc_reverse': Jsc_f, 'Jsc_forwards': Jsc_b, 'Voc_reverse': Voc_f, 'Voc_forwards': Voc_b, 'Hysteresis_Index_reverse': hysteresis_index}
    df1 = pd.DataFrame(dict)
    df1.to_csv(ablage, index=False)
    
    return ablage
    
###         MASTERCODE2         ######
# Datei einlesen
file_path = Datenauslesen()
df = pd.read_csv(file_path)

#speichern
global save_path
save_path = path_entry

# funktion kriegt dataframe, strings und spalten. schaut in welchen zeilen der 0. spalte die namen strings auftauchen und returned ein dataframe mit booleans
def group_by_new_criteria(df, prefixes, spalte, min_value=None):
    data = []
    for prefix in prefixes:
        mask = df.iloc[:, 0].str.contains(prefix)
        group = df[mask]
        if not group.empty:
            values = group.iloc[:, spalte+1].values
            data.extend(values)

    return data

group_labels = [item[0] for item in global_name_lists]

# Gruppierungen festlegen      das ist ne iteration über global_string_lists
daten_ablegen = []
wirklich_alle = []
    
for spalte in range(0,9):       
    for i in range(len(global_string_lists)):      
        daten_ablegen.append(group_by_new_criteria(df, global_string_lists[i], spalte))
    hilfsliste3 = [daten_ablegen[k] for k in range(len(global_string_lists))]
    wirklich_alle.append(hilfsliste3)
    daten_ablegen.clear()
        
def clean_nested_data(data, min_values, max_values):
    # Anzahl der Gruppen und Untergruppen bestimmen
    num_groups = len(data) 
    num_subgroups = len(data[0])  

    # Bereinigte Datenstruktur erstellen (eine tiefe Kopie des Originaldatensatzes)
    cleaned_data = [[[subgroup[i] for i in range(len(subgroup))] for subgroup in group] for group in data]

    # Datenbereinigung durchführen
    for i in range(num_groups):
        for j in range(num_subgroups):
            for k in range(len(data[i][j])):
                value = data[i][j][k] 
                # Prüfen, ob der Wert außerhalb des zulässigen Bereichs liegt
                if value < min_values[i] or value > max_values[i]:
                    # Wert aus allen Gruppen an der gleichen Position entfernen
                    for g in range(num_groups):
                        if k < len(cleaned_data[g][j]):
                            cleaned_data[g][j][k] = None

    # Entferne None-Werte aus den bereinigten Daten
    for i in range(num_groups):
        for j in range(num_subgroups):
            cleaned_data[i][j] = [val for val in cleaned_data[i][j] if val is not None]

    return cleaned_data

cleaned = clean_nested_data(wirklich_alle, global_min_values, global_max_values)

### create one list with best and one list for median reverse PCE value for each variation
reverse_best = []
reverse_median = []

for i in range(len(cleaned[0])):
    reverse_best.append(max(cleaned[0][i]))
    n = len(cleaned[0][i])
    sauber = sorted(cleaned[0][i]) #startet mit höchster zahl
    reverse_median.append(sauber[n // 2]) #da die anzahl gerade ist, wird der median +1 ausgewählt


def plotting(cleaned, group_labels):
    yachsenname = ['PCE [%]',0, 'FF [%]',0, r'J$_{\text{sc}}$ [mA/cm$^2$]',0, r'V$_{\text{oc}}$ [V]',0, 'Hysteresis Index']
    #zuerst gemischter plot ohne hysterese
    plt.figure(figsize=(20, 12))
    
    for daten in range(0,8,2):
        # Initialisiere leere Listen
        pairs = []
        groups = []
        values = []
        
        # Daten in Listen umwandeln
        for i in range(len(cleaned[0])):
            for j in range(len(cleaned[daten][i])):
                pairs.append(group_labels[i])
                groups.append('reverse')
                values.append(cleaned[daten][i][j])

                pairs.append(group_labels[i])
                groups.append('forward')
                values.append(cleaned[daten+1][i][j])

        # Daten in DataFrame umwandeln
        sf = pd.DataFrame({
            'Paar': pairs,
            'Gruppe': groups,
            'Wert': values
        })

        # Erstelle den Boxplot
        plt.subplot(2, 2, (int(daten/2))+1)
        sns.boxplot(x='Paar', y='Wert', hue='Gruppe', data=sf)
        if global_boolean:
            sns.stripplot(x='Paar', y='Wert', hue='Gruppe', data=sf, dodge=True, jitter=True, palette='dark:black', alpha=0.5, legend=False)
        #plotkram
        plt.ylabel(yachsenname[daten], fontsize = 24)
        if daten == 0 or daten == 2:
            plt.xticks([]) 
        else:
            plt.xticks(range(len(group_labels)), group_labels, fontsize = 19)
        plt.xlabel("")
        plt.yticks(fontsize=18)
        plt.legend(fontsize=16)
    plt.tight_layout()
    plt.savefig(save_path+"/"+name_entry+"_snsplot.png", dpi = 1500) 
    plt.show()
    
    #hier gehts jetzt mit der hysterese weiter (ctrl+c/ctrl+v ansatz)
    if global_boolean5:
        daten = 8
    
        pairs = []
        groups = []
        values = []
           
        # Daten in Listen umwandeln
        for i in range(len(cleaned[0])):
            for j in range(len(cleaned[daten][i])):
                pairs.append(group_labels[i])
                groups.append('test')
                values.append(cleaned[daten][i][j])
    
        # Daten in DataFrame umwandeln
        sf = pd.DataFrame({
            'Paar': pairs,
            'Gruppe': groups,
            'Wert': values
        })
        
        # Erstelle den Boxplot
        sns.boxplot(x='Paar', y='Wert', hue='Gruppe', data=sf, legend = False)
        if global_boolean:
            sns.stripplot(x='Paar', y='Wert', hue='Gruppe', data=sf, dodge=True, jitter=True, palette='dark:black', alpha=0.5, legend = False)
        plt.ylabel(yachsenname[daten], fontsize = 24)
        if daten == 0 or daten == 2:
            plt.xticks([]) 
        else:
            plt.xticks(range(len(group_labels)), group_labels, fontsize = 19)
        plt.xlabel("")
        plt.yticks(fontsize=18)
        plt.tight_layout()
        plt.savefig(save_path+"/"+name_entry+"_hysterese.png", dpi = 1500) 
   
plotting(cleaned, group_labels)

if global_boolean4:
    inverting = -1
else:
    inverting = 1
    
#find the data for the median or best PCE

def finde_dateiname(df, liste, bestormedian):
   
    # Sicherstellen, dass die relevanten Spalten vorhanden sind
    if 'PSC_reverse' not in df.columns or 'filename' not in df.columns:
        raise ValueError("Der DataFrame muss die Spalten 'PSC_reverse' und 'filename' enthalten.")
    
    # Filtern nach übereinstimmenden Werten in der Spalte 'PSC_reverse'
    result = df[df['PSC_reverse'].isin(liste)]['filename']
    
    # Die entsprechenden 'filename'-Werte als Liste zurückgeben
    plot(result.tolist(), bestormedian)
    return

    
#JV plotting

def plot(pfad_list, bestormedian):
    # Überprüfen, ob pfad_list eine Liste ist
    if not isinstance(pfad_list, list):
        raise ValueError("Der Parameter 'pfad_list' muss eine Liste von Strings sein.")

    # Abbildung erstellen
    plt.figure(figsize=(10, 7))

    # Jeden Pfad in der Liste iterieren
    for i,pfad in enumerate(pfad_list,start=0): #iteriert integer über i und pfadstrings über pfad
        # Pfad zur Datei anpassen
        file_path = path_entry + "/" + str(pfad)
        
        # Originaldatei laden, um die Zahlen in Zeile 9 zu extrahieren
        with open(file_path, 'r', encoding='latin1') as file:
            lines = file.readlines()
            line_6 = lines[5]
            line_7 = lines[6]
            line_8 = lines[7]
            line_9 = lines[8]  # Index 8 entspricht der 9. Zeile (0-basiert)
        Jsc = line_6.split()
        Voc = line_7.split()
        FF = line_8.split()
        eff = line_9.split() 
        
        # Datei laden und die ersten 12 Zeilen überspringen
        data = pd.read_csv(file_path, encoding='latin1', delimiter='\t', skiprows=12) 

        # Spaltennamen anpassen, falls nötig 
        data.columns = ['X', 'Y1', 'Y2', 'Y3'] #klassischerweise soll Y2 

        print(f"best or median: f{bestormedian}, variation: f{group_labels[i]}, path: {pfad} \n")
        # Plotten der Daten
        plt.plot(inverting*data['X'], inverting*data['Y1'], marker='o', linestyle='-', 
                 label=f"label: {group_labels[i]}\n" +
                       f"Jsc: {round(float(Jsc[2]), 2)} mA/cm$^2$\n" +
                       f"Voc: {round(float(Voc[2]), 2)} V\n" +
                       f"FF: {round(float(FF[2]), 2)} %\n" +
                       f"PCE: {round(float(eff[1]), 2)} %")
        #plt.plot(inverting*data['X'], inverting*data['Y2'], marker='x', linestyle='--', 
        #         label=f"{pfad} forward:\n" +
        #               f"Jsc: {round(float(Jsc[3]), 2)} mA/cm$^2$\n" +
        #               f"Voc: {round(float(Voc[3]), 2)} V\n" +
        #               f"FF: {round(float(FF[3]), 2)} %\n" +
        #               f"PCE: {round(float(eff[2]), 2)} %")

    # Achsentitel und Layout
    plt.xlabel('voltage [V]', fontsize=18)
    plt.ylabel(f'{bestormedian} current density [mA/cm$^2$]', fontsize=18)
    plt.axhline(y=0, color='black', linestyle='dashed')
    plt.legend(fontsize=12, framealpha=1, facecolor='white')
    plt.xticks(fontsize=18)
    plt.yticks(fontsize=18)
    plt.tight_layout()

    # Abbildung speichern
    plt.savefig(save_path + "/" + name_entry + "_reverse_JV_" + str(bestormedian) + ".png", dpi=1000)

if global_boolean2:
    finde_dateiname(df, reverse_best, 'best')
if global_boolean3:
    finde_dateiname(df, reverse_median, 'median')

