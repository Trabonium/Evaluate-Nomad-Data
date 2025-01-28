import tkinter as tk
from tkinter import ttk
import pandas as pd

# Globale Variable für df_min_max_self
#df_min_max_self = pd.DataFrame()

# Funktion, um die Dual-Slider zu erstellen
def create_dual_slider(parent, title, min_val, max_val, init_min, init_max, slider_id, update_df_func):
    frame = ttk.Frame(parent)
    frame.pack(fill=tk.X, padx=20, pady=10)

    title_label = ttk.Label(frame, text=title)
    title_label.pack(pady=5, padx=10)

    canvas_width = 350
    canvas = tk.Canvas(frame, height=50, width=canvas_width)
    canvas.pack(pady=5)

    # Zeichne die Slider-Leiste
    canvas.create_line(10, 20, canvas_width - 10, 20, fill="grey", width=4)

    # Initiale Positionen
    init_min_pos = 10 + ((init_min - min_val) / (max_val - min_val)) * (canvas_width - 20)
    init_max_pos = 10 + ((init_max - min_val) / (max_val - min_val)) * (canvas_width - 20)

    slider1 = canvas.create_line(init_min_pos, 10, init_min_pos, 30, fill="blue", width=3)
    slider2 = canvas.create_line(init_max_pos, 10, init_max_pos, 30, fill="red", width=3)

    # Funktionen für die Slider
    def move_slider1(event):
        x = event.x
        if 10 <= x <= canvas.coords(slider2)[0]:  # Slider1 darf nicht rechts von Slider2 sein
            new_min = min_val + ((x - 10) / (canvas_width - 20)) * (max_val - min_val)
            canvas.coords(slider1, x, 10, x, 30)
            update_df_func(slider_id, 'Min', new_min)
            update_label()

    def move_slider2(event):
        x = event.x
        if canvas.coords(slider1)[0] <= x <= canvas_width - 10:  # Slider2 darf nicht links von Slider1 sein
            new_max = min_val + ((x - 10) / (canvas_width - 20)) * (max_val - min_val)
            canvas.coords(slider2, x, 10, x, 30)
            update_df_func(slider_id, 'Max', new_max)
            update_label()

    # Aktualisiere Labels und Eingabefelder
    def update_label():
        current_min = df_min_max_self.at[slider_id, 'Min']
        current_max = df_min_max_self.at[slider_id, 'Max']
        min_var.set(round(current_min, 2))
        max_var.set(round(current_max, 2))

    # Aktualisiere Schieberegler aus Eingabefeldern
    def update_from_entry(event=None):
        try:
            new_min = float(min_var.get())
            new_max = float(max_var.get())

            # Stellen sicher, dass der Wert innerhalb der Min/Max Grenzen liegt
            if min_val <= new_min <= max_val and new_min <= df_min_max_self.at[slider_id, 'Max']:
                x_min = 10 + ((new_min - min_val) / (max_val - min_val)) * (canvas_width - 20)
                canvas.coords(slider1, x_min, 10, x_min, 30)
                update_df_func(slider_id, 'Min', new_min)

            if min_val <= new_max <= max_val and new_max >= df_min_max_self.at[slider_id, 'Min']:
                x_max = 10 + ((new_max - min_val) / (max_val - min_val)) * (canvas_width - 20)
                canvas.coords(slider2, x_max, 10, x_max, 30)
                update_df_func(slider_id, 'Max', new_max)

            update_label()
        except ValueError:
            pass

    # Variablen für Eingabefelder
    min_var = tk.StringVar(value=str(init_min))
    max_var = tk.StringVar(value=str(init_max))

    # Eingabefelder
    entry_frame = ttk.Frame(frame)
    entry_frame.pack(pady=10)

    min_entry = ttk.Entry(entry_frame, textvariable=min_var, width=10)
    min_entry.pack(side=tk.LEFT, padx=5)
    min_entry.bind("<Return>", update_from_entry)

    max_entry = ttk.Entry(entry_frame, textvariable=max_var, width=10)
    max_entry.pack(side=tk.LEFT, padx=5)
    max_entry.bind("<Return>", update_from_entry)

    # Binde Mausereignisse an die Schieberegler
    canvas.tag_bind(slider1, "<B1-Motion>", move_slider1)
    canvas.tag_bind(slider2, "<B1-Motion>", move_slider2)

    # Aktualisiere Labels initial
    update_label()

    return frame


# Funktion, um die Schieberegler und den Speichern-Button hinzuzufügen
def open_sliders_window(filter_window, df_min_max_bounds):
    # Rahmen für Scrollbereich erstellen
    container = ttk.Frame(filter_window)
    container.pack(fill="both", expand=True)

    # Canvas mit Scrollbar erstellen
    canvas = tk.Canvas(container)
    scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
    scrollable_frame = ttk.Frame(canvas)

    # Scrollable Frame konfigurieren
    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )

    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    # Platzierung der Canvas und Scrollbar
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    def _on_mouse_wheel(event):
        canvas.yview_scroll(-1 * int(event.delta / 120), "units")  # Für Windows und macOS

    canvas.bind_all("<MouseWheel>", _on_mouse_wheel)

    # Schieberegler erstellen
    for i, row in df_min_max_bounds.iterrows():
        create_dual_slider(
            scrollable_frame,
            title=row['Parameter'],
            min_val=row['Min'],
            max_val=row['Max'],
            init_min=row['Min'],
            init_max=row['Max'],
            slider_id=i,
            update_df_func=update_df_func
        )

    # Speichern-Button hinzufügen
    def save_and_close():
        filter_window.destroy()  # Fenster schließen

    save_button = ttk.Button(scrollable_frame, text="Save", command=save_and_close)
    save_button.pack(pady=20)



# Funktion zum Starten des Programms
def schieberegler_main(filter_window, filtered_df):
    global df_min_max_self

    # Erstelle df_min_max_bounds mit Min- und Max-Werten
    df_min_max_bounds = pd.DataFrame(columns=["Parameter", "Min", "Max"])

    df_min_max_bounds["Parameter"] = ["PCE", "FF", "Voc", "Jsc"]
    df_min_max_bounds["Min"] = [
        min(filtered_df["efficiency"].tolist()),
        min(filtered_df["fill_factor"].tolist()),
        min(filtered_df["open_circuit_voltage"].tolist()),
        min(filtered_df["short_circuit_current_density"].tolist()),
    ]
    df_min_max_bounds["Max"] = [
        max(filtered_df["efficiency"].tolist()),
        max(filtered_df["fill_factor"].tolist()),
        max(filtered_df["open_circuit_voltage"].tolist()),
        max(filtered_df["short_circuit_current_density"].tolist()),
    ]

    df_min_max_self = df_min_max_bounds.copy()

    open_sliders_window(filter_window, df_min_max_bounds)


# Update-Funktion für den DataFrame
def update_df_func(slider_id, param, value):
    df_min_max_self.at[slider_id, param] = value

def main_filter(df_default_werte, master):
    filtered_df = df_default_werte.copy() #zuerst kopie definieren
    # NaNs rauswerfen
    filtered_df = filtered_df.dropna(subset=['efficiency'])
    filtered_df = filtered_df.dropna(subset=['fill_factor'])
    filtered_df = filtered_df.dropna(subset=['open_circuit_voltage'])
    filtered_df = filtered_df.dropna(subset=['short_circuit_current_density'])

    filter_window = tk.Toplevel(master)
    filter_window.title("Dual Sliders")
    filter_window.geometry("400x700")

    schieberegler_main(filter_window, filtered_df) #hier werden die grenzenn zum filtern gesetzt

    filter_window.grab_set()
    filter_window.wait_window()
    
    # Tkinter Mainloop starten

    #filtergrößen:
    min_pce = df_min_max_self[df_min_max_self["Parameter"] == "PCE"]["Min"].values[0]
    max_pce = df_min_max_self[df_min_max_self["Parameter"] == "PCE"]["Max"].values[0]
    min_ff = df_min_max_self[df_min_max_self["Parameter"] == "FF"]["Min"].values[0]
    max_ff = df_min_max_self[df_min_max_self["Parameter"] == "FF"]["Max"].values[0]
    min_jsc = df_min_max_self[df_min_max_self["Parameter"] == "Jsc"]["Min"].values[0]
    max_jsc = df_min_max_self[df_min_max_self["Parameter"] == "Jsc"]["Max"].values[0]
    min_voc = df_min_max_self[df_min_max_self["Parameter"] == "Voc"]["Min"].values[0]
    max_voc = df_min_max_self[df_min_max_self["Parameter"] == "Voc"]["Max"].values[0]

    #nach NaN filter jetzt aktiveer datenfilter
    filtered_df = filtered_df[(filtered_df['efficiency'] >= min_pce) & (filtered_df['efficiency'] <= max_pce)]
    filtered_df = filtered_df[(filtered_df['fill_factor'] >= min_ff) & (filtered_df['fill_factor'] <= max_ff)]
    filtered_df = filtered_df[(filtered_df['open_circuit_voltage'] >= min_voc) & (filtered_df['open_circuit_voltage'] <= max_voc)]
    filtered_df = filtered_df[(filtered_df['short_circuit_current_density'] >= min_jsc) & (filtered_df['short_circuit_current_density'] <= max_jsc)]
    return(filtered_df)
