import tkinter as tk
from tkinter import ttk
import pandas as pd
from datetime import datetime, timedelta
from tkinter import messagebox

global cycle_optimizing
cycle_optimizing = False

def parse_datetime_safe(dt_str):
    """Parse datetime string handling both ISO format (with T) and simple format"""
    try:
        if 'T' in dt_str:
            # ISO format: '2025-08-21T12:01:28+00:00'
            # Parse and ignore timezone for local comparison
            return pd.to_datetime(dt_str).replace(tzinfo=None)
        else:
            # Simple format: '2025-08-21 13:01'
            return pd.to_datetime(dt_str)
    except:
        return None

def filter_best_efficiency(df):  
    # Index der Zeilen mit maximaler Effizienz je Gruppe finden
    idx = df.groupby(['sample_id', 'variation', 'px#', 'scan_direction'])['efficiency'].idxmax()

    # Nur diese Zeilen behalten (Reihenfolge bleibt wie im Original-DF)
    df_filtered = df.loc[idx].sort_index()

    return df_filtered

def create_cycle_buttons(parent, cycles, filtered_df):
    frame = ttk.Frame(parent)
    frame.pack(fill=tk.X, padx=20, pady=10)

    title_label = ttk.Label(frame, text="Cycle Filter")
    title_label.pack(pady=5, padx=10)

    buttons = {}

    # Variable für Checkbox
    best_efficiency_var = tk.BooleanVar(value=False)

    # Funktion zum Umschalten der Buttons
    def toggle_cycle(cycle):
        if best_efficiency_var.get():  # Wenn Checkbox aktiv ist, kein Umschalten erlauben
            return

        if cycle not in filtered_df["Cycle#"].values:
            print(f"Warnung: Cycle {cycle} not found in data!")
            return

        current_status = filtered_df.loc[filtered_df["Cycle#"] == cycle, "cyclefilter"]
        if not current_status.empty:
            new_status = not current_status.iloc[0]  # Wechsel zwischen True/False
            filtered_df.loc[filtered_df["Cycle#"] == cycle, "cyclefilter"] = new_status
            buttons[cycle]["bg"] = "red" if not new_status else "green"
            #print(f"Cycle {cycle} ist jetzt {'aktiv' if new_status else 'deaktiviert'}")

    # Funktion für die Checkbox
    def toggle_best_efficiency():
        global cycle_optimizing
        if best_efficiency_var.get():
            cycle_optimizing = True
            for btn in buttons.values():
                btn.config(bg="gray", state=tk.DISABLED)  # Buttons deaktivieren und grau färben
        else:
            cycle_optimizing = False
            for cycle, btn in buttons.items():
                btn.config(bg="green", state=tk.NORMAL)  # Buttons aktivieren und zurücksetzen

    # Checkbox erstellen
    checkbox = ttk.Checkbutton(frame, text="Only best cycle?", variable=best_efficiency_var, command=toggle_best_efficiency)
    checkbox.pack(pady=5)

    # Button-Frame erstellen
    button_frame = ttk.Frame(frame)
    button_frame.pack()

    for cycle in sorted(cycles):
        btn = tk.Button(button_frame, text=str(cycle), bg="green", width=5, command=lambda c=cycle: toggle_cycle(c))
        btn.pack(side=tk.LEFT, padx=5)
        buttons[cycle] = btn

    return best_efficiency_var  # Checkbox-Variable zurückgeben

# Funktion, um die Dual-Slider zu erstellen
def create_dual_slider(parent, title, min_val, max_val, init_min, init_max, slider_id, update_df_func, first_slider):
    frame = ttk.Frame(parent)
    frame.pack(fill=tk.X, padx=20, pady=10)

    # Horizontale Trennlinie nur hinzufügen, wenn es nicht der erste Slider ist
    if not first_slider:
        separator = ttk.Separator(frame, orient="horizontal")
        separator.pack(fill=tk.X, padx=20, pady=5)

    title_label = ttk.Label(frame, text=title)
    title_label.pack(pady=5, padx=10)

    canvas_width = 350
    canvas = tk.Canvas(frame, height=50, width=canvas_width)
    canvas.pack(pady=5)

    # Zeichne die Slider-Leiste
    canvas.create_line(10, 20, canvas_width - 10, 20, fill="grey", width=4)

    # Handle datetime objects for slider calculations
    if title == "Datetime":
        # Convert datetime objects to timestamps for slider positioning
        if isinstance(min_val, pd.Timestamp):
            min_val_calc = min_val.timestamp()
            max_val_calc = max_val.timestamp()
            init_min_calc = init_min.timestamp()
            init_max_calc = init_max.timestamp()
        else:
            min_val_calc = min_val.timestamp() if hasattr(min_val, 'timestamp') else min_val
            max_val_calc = max_val.timestamp() if hasattr(max_val, 'timestamp') else max_val
            init_min_calc = init_min.timestamp() if hasattr(init_min, 'timestamp') else init_min
            init_max_calc = init_max.timestamp() if hasattr(init_max, 'timestamp') else init_max
    else:
        min_val_calc = min_val
        max_val_calc = max_val
        init_min_calc = init_min
        init_max_calc = init_max

    # Initiale Positionen
    init_min_pos = 10 + ((init_min_calc - min_val_calc) / (max_val_calc - min_val_calc)) * (canvas_width - 20)
    init_max_pos = 10 + ((init_max_calc - min_val_calc) / (max_val_calc - min_val_calc)) * (canvas_width - 20)
    init_max_pos = 10 + ((init_max_calc - min_val_calc) / (max_val_calc - min_val_calc)) * (canvas_width - 20)

    slider1 = canvas.create_line(init_min_pos, 10, init_min_pos, 30, fill="blue", width=3)
    slider2 = canvas.create_line(init_max_pos, 10, init_max_pos, 30, fill="red", width=3)

    # Funktionen für die Slider
    def move_slider1(event):
        x = event.x
        if 10 <= x <= canvas.coords(slider2)[0]:  # Slider1 darf nicht rechts von Slider2 sein
            if title == "Datetime":
                # Calculate new datetime value
                ratio = (x - 10) / (canvas_width - 20)
                new_timestamp = min_val_calc + ratio * (max_val_calc - min_val_calc)
                new_min = datetime.fromtimestamp(new_timestamp)
            else:
                new_min = min_val + ((x - 10) / (canvas_width - 20)) * (max_val - min_val)
            canvas.coords(slider1, x, 10, x, 30)
            update_df_func(slider_id, 'Min', new_min)
            update_label()

    def move_slider2(event):
        x = event.x
        if canvas.coords(slider1)[0] <= x <= canvas_width - 10:  # Slider2 darf nicht links von Slider1 sein
            if title == "Datetime":
                # Calculate new datetime value
                ratio = (x - 10) / (canvas_width - 20)
                new_timestamp = min_val_calc + ratio * (max_val_calc - min_val_calc)
                new_max = datetime.fromtimestamp(new_timestamp)
            else:
                new_max = min_val + ((x - 10) / (canvas_width - 20)) * (max_val - min_val)
            canvas.coords(slider2, x, 10, x, 30)
            update_df_func(slider_id, 'Max', new_max)
            update_label()

    # Aktualisiere Labels und Eingabefelder
    def update_label():
        current_min = df_min_max_self.at[slider_id, 'Min']
        current_max = df_min_max_self.at[slider_id, 'Max']
        
        # Special handling for datetime display
        if title == "Datetime":
            # current_min and current_max are now datetime objects, not timestamps
            if isinstance(current_min, pd.Timestamp):
                min_date = current_min.to_pydatetime()
                max_date = current_max.to_pydatetime()
            else:
                min_date = current_min
                max_date = current_max
            min_var.set(min_date.strftime("%Y-%m-%d %H:%M"))
            max_var.set(max_date.strftime("%Y-%m-%d %H:%M"))
        else:
            min_var.set(current_min)
            max_var.set(current_max)

    # Aktualisiere Schieberegler aus Eingabefeldern
    def update_from_entry(event=None):
        try:
            if title == "Datetime":
                # Handle datetime input - keep as datetime objects, not timestamps
                new_min = datetime.strptime(min_var.get(), "%Y-%m-%d %H:%M")
                new_max = datetime.strptime(max_var.get(), "%Y-%m-%d %H:%M")
                
                # For slider positioning, we need to convert to timestamps temporarily
                new_min_ts = new_min.timestamp()
                new_max_ts = new_max.timestamp()
                
                # Check bounds using timestamps
                if min_val_calc <= new_min_ts <= max_val_calc and new_min_ts <= df_min_max_self.at[slider_id, 'Max'].timestamp():
                    x_min = 10 + ((new_min_ts - min_val_calc) / (max_val_calc - min_val_calc)) * (canvas_width - 20)
                    canvas.coords(slider1, x_min, 10, x_min, 30)
                    update_df_func(slider_id, 'Min', new_min)  # Store datetime object

                if min_val_calc <= new_max_ts <= max_val_calc and new_max_ts >= df_min_max_self.at[slider_id, 'Min'].timestamp():
                    x_max = 10 + ((new_max_ts - min_val_calc) / (max_val_calc - min_val_calc)) * (canvas_width - 20)
                    canvas.coords(slider2, x_max, 10, x_max, 30)
                    update_df_func(slider_id, 'Max', new_max)  # Store datetime object
            else:
                # Handle numeric input
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
    if title == "Datetime":
        # init_min and init_max are now datetime objects, not timestamps
        if isinstance(init_min, pd.Timestamp):
            init_min_date = init_min.to_pydatetime()
            init_max_date = init_max.to_pydatetime()
        else:
            init_min_date = init_min
            init_max_date = init_max
        min_var = tk.StringVar(value=init_min_date.strftime("%Y-%m-%d %H:%M"))
        max_var = tk.StringVar(value=init_max_date.strftime("%Y-%m-%d %H:%M"))
        entry_width = 15
    else:
        min_var = tk.StringVar(value=str(init_min))
        max_var = tk.StringVar(value=str(init_max))
        entry_width = 10

    # Eingabefelder
    entry_frame = ttk.Frame(frame)
    entry_frame.pack(pady=10)

    min_entry = ttk.Entry(entry_frame, textvariable=min_var, width=entry_width)
    min_entry.pack(side=tk.LEFT, padx=5)
    min_entry.bind("<Return>", update_from_entry)

    max_entry = ttk.Entry(entry_frame, textvariable=max_var, width=entry_width)
    max_entry.pack(side=tk.LEFT, padx=5)
    max_entry.bind("<Return>", update_from_entry)

    # Binde Mausereignisse an die Schieberegler
    canvas.tag_bind(slider1, "<B1-Motion>", move_slider1)
    canvas.tag_bind(slider2, "<B1-Motion>", move_slider2)

    # Aktualisiere Labels initial
    update_label()

    return frame


# Funktion, um die Schieberegler und den Speichern-Button hinzuzufügen
def open_sliders_window(filter_window, df_min_max_bounds, master, cycles, filtered_df):
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
        # Use same function for all parameters, including datetime
        create_dual_slider(
            scrollable_frame,
            title=row['Parameter'],
            min_val=row['Min'],
            max_val=row['Max'],
            init_min=row['Min'],
            init_max=row['Max'],
            slider_id=i,
            update_df_func=update_df_func, 
            first_slider=(i==0)
        )

    print(f"Cycles available: {cycles}")
    if cycles is not None and len(cycles) > 0:
        print("Creating cycle buttons...")
        filtered_df["Cycle#"] = filtered_df["Cycle#"].astype(int)  # Erzwinge `int`-Typisierung
        best_efficiency_var = create_cycle_buttons(scrollable_frame, cycles, filtered_df)
    else:
        print("No cycles found or cycles is None")
        best_efficiency_var = False

    
    # Speichern-Button hinzufügen
    def save_and_close():
        filter_window.destroy()

    save_button = ttk.Button(scrollable_frame, text="Save", command=save_and_close)
    save_button.pack(pady=20)

    return best_efficiency_var

# Funktion zum Starten des Programms
def schieberegler_main(filter_window, filtered_df, master, cycles):
    global df_min_max_self

    # Erstelle df_min_max_bounds mit Min- und Max-Werten
    df_min_max_bounds = pd.DataFrame(columns=["Parameter", "Min", "Max"])

    # Standard Parameter
    parameters = ["PCE", "FF", "Voc", "Jsc"]
    min_values = [
        min(filtered_df["efficiency"].tolist()),
        min(filtered_df["fill_factor"].tolist()),
        min(filtered_df["open_circuit_voltage"].tolist()),
        min(filtered_df["short_circuit_current_density"].tolist()),
    ]
    max_values = [
        max(filtered_df["efficiency"].tolist()),
        max(filtered_df["fill_factor"].tolist()),
        max(filtered_df["open_circuit_voltage"].tolist()),
        max(filtered_df["short_circuit_current_density"].tolist()),
    ]

    # Prüfen ob datetime-Spalte vorhanden ist und gültige Daten enthält
    if 'datetime' in filtered_df.columns:
        try:
            # Don't convert here, just check if datetime data exists
            datetime_data = filtered_df['datetime'].dropna()
            if len(datetime_data) > 0:
                # Convert to timezone-naive datetime objects (treat as local time)
                datetime_series = pd.to_datetime(datetime_data)
                min_datetime_raw = datetime_series.min()
                max_datetime_raw = datetime_series.max()
                
                # Widen bounds significantly to ensure no data loss when slider is not moved
                # Subtract 1 hour from min, add 1 hour to max
                min_datetime = min_datetime_raw - pd.Timedelta(hours=1)
                max_datetime = max_datetime_raw + pd.Timedelta(hours=1)
                
                # Round to nice boundaries
                min_datetime = min_datetime.replace(second=0, microsecond=0)
                max_datetime = max_datetime.replace(second=0, microsecond=0)
                
                # Store datetime objects directly instead of timestamps to avoid timezone conversion
                # We'll convert to string format for comparison later
                #min_timestamp = min_datetime  # Keep as datetime object
                #max_timestamp = max_datetime  # Keep as datetime object
                
                # Datetime als ersten Parameter hinzufügen
                parameters.insert(0, "Datetime")
                min_values.insert(0, min_datetime)
                max_values.insert(0, max_datetime)
                print(f"Added datetime filter with wide bounds: {min_datetime} to {max_datetime}")
                print(f"Original data range: {min_datetime_raw} to {max_datetime_raw}")
        except Exception as e:
            print(f"Error processing datetime column: {e}")

    df_min_max_bounds["Parameter"] = parameters
    df_min_max_bounds["Min"] = min_values
    df_min_max_bounds["Max"] = max_values

    df_min_max_self = df_min_max_bounds.copy()

    best_efficiency_var = open_sliders_window(filter_window, df_min_max_bounds, master, cycles, filtered_df)

    return best_efficiency_var

# Update-Funktion für den DataFrame
def update_df_func(slider_id, param, value):
    df_min_max_self.at[slider_id, param] = value

def main_filter(df_default_werte, master):
    global cycle_optimizing
    
    filtered_df = df_default_werte.copy() #zuerst kopie definieren
    filtered_df['cyclefilter'] = True

    # NaNs entfernen
    filtered_df = filtered_df.dropna(subset=['efficiency', 'fill_factor', 'open_circuit_voltage', 'short_circuit_current_density'])

    filter_window = tk.Toplevel(master)
    filter_window.title("Data Filters")
    filter_window.geometry("400x800")

    cycles = None
    #print(filtered_df.columns)

    if "Cycle#" in filtered_df.columns and filtered_df["Cycle#"].notna().all():
        cycles = filtered_df["Cycle#"].dropna().unique().astype(int)

    best_efficiency_var = schieberegler_main(filter_window, filtered_df, master, cycles) #hier werden die grenzenn zum filtern gesetzt

    filter_window.grab_set(),
    filter_window.wait_window()

    #print("jetzt richtig?: ", cycle_optimizing)

    # Apply datetime filter if datetime parameter exists
    datetime_row = df_min_max_self[df_min_max_self["Parameter"] == "Datetime"]
    if not datetime_row.empty and 'datetime' in filtered_df.columns:
        try:
            # Get datetime filter values (already datetime objects)
            min_filter_dt = datetime_row["Min"].values[0]
            max_filter_dt = datetime_row["Max"].values[0]
            
            # Convert pd.Timestamp to datetime if needed
            if isinstance(min_filter_dt, pd.Timestamp):
                min_filter_dt = min_filter_dt.to_pydatetime()
                max_filter_dt = max_filter_dt.to_pydatetime()
            
            print(f"Datetime filter range: {min_filter_dt.strftime('%Y-%m-%d %H:%M')} to {max_filter_dt.strftime('%Y-%m-%d %H:%M')}")
            
            original_count = len(filtered_df)
            
            # Parse data datetime strings and filter using proper datetime comparison
            filtered_df['datetime_parsed'] = filtered_df['datetime'].apply(parse_datetime_safe)
            filtered_df = filtered_df[filtered_df['datetime_parsed'].notna()]  # Remove unparseable dates
            
            # Filter using datetime objects (proper semantic comparison)
            filtered_df = filtered_df[
                (filtered_df['datetime_parsed'] >= min_filter_dt) & 
                (filtered_df['datetime_parsed'] <= max_filter_dt)
            ]
            
            # Clean up temporary column
            filtered_df = filtered_df.drop(columns=['datetime_parsed'])
            
            print(f"Datetime filter applied: {original_count} -> {len(filtered_df)} rows")
            
        except Exception as e:
            print(f"Error applying datetime filter: {e}")

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
    print(f"Before performance filters: {len(filtered_df)} rows")
    filtered_df = filtered_df[(filtered_df['efficiency'] >= min_pce) & (filtered_df['efficiency'] <= max_pce)]
    filtered_df = filtered_df[(filtered_df['fill_factor'] >= min_ff) & (filtered_df['fill_factor'] <= max_ff)]
    filtered_df = filtered_df[(filtered_df['open_circuit_voltage'] >= min_voc) & (filtered_df['open_circuit_voltage'] <= max_voc)]
    filtered_df = filtered_df[(filtered_df['short_circuit_current_density'] >= min_jsc) & (filtered_df['short_circuit_current_density'] <= max_jsc)]
    print(f"After performance filters: {len(filtered_df)} rows")
    
    if 'datetime' in filtered_df.columns and len(filtered_df) > 0:
        print(f"Datetime range after performance filters: {filtered_df['datetime'].min()} to {filtered_df['datetime'].max()}")
    
    if filtered_df['Cycle#'].isna().all():
        cycle_optimizing = False

    if cycle_optimizing:
        print("Applying best cycle filter...")
        print(f"Before best cycle filter: {len(filtered_df)} rows")
        filtered_df = filter_best_efficiency(filtered_df)
        print(f"After best cycle filter: {len(filtered_df)} rows")
    else:
        if filtered_df["Cycle#"].notna().all():
            print("Applying cycle selection filter...")
            print(f"Before cycle selection filter: {len(filtered_df)} rows")
            filtered_df = filtered_df[filtered_df["cyclefilter"] == True]  # Nur aktive Zyklen behalten
            print(f"After cycle selection filter: {len(filtered_df)} rows")
    
    if 'datetime' in filtered_df.columns and len(filtered_df) > 0:
        print(f"Final datetime range: {filtered_df['datetime'].min()} to {filtered_df['datetime'].max()}")
        
    filtered_df = filtered_df.drop(columns=["cyclefilter"])  # Spalte entfernen, bevor DataFrame zurückgegeben wird

    #if the column 'Cycles#' are just Nones, the plotting function cant plot the scatter plot
    #if filtered_df["Cycle#"].isna().all():
    #    best_efficiency_var = True

    return(filtered_df, df_min_max_self, cycle_optimizing)
