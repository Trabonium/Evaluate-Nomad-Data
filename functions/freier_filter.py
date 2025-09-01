import tkinter as tk
from tkinter import ttk
import pandas as pd

def freier_filter(df, master):
    filter_window = tk.Toplevel(master)
    filter_window.title("Datenansicht")
    filter_window.geometry("800x400")

    # Zustand
    grayed_indices = set()
    auto_nan_checked = tk.BooleanVar(value=False)
    nan_relevant_cols = [
        "efficiency",
        "fill_factor",
        "open_circuit_voltage",
        "short_circuit_current_density"
    ]

    # Treeview erstellen
    frame = tk.Frame(filter_window)
    frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

    tree = ttk.Treeview(frame, columns=['Index'] + list(df.columns), show='headings', selectmode='extended')
    tree.heading('Index', text='Index')
    tree.column('Index', width=50)

    for col in df.columns:
        tree.heading(col, text=col)
        tree.column(col, width=120)

    for i, row in df.iterrows():
        tree.insert("", tk.END, values=[i] + list(row))

    tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    scrollbar = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    tree.configure(yscroll=scrollbar.set)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    # Unterstütze Shift-Auswahl mit Maus
    def on_click(event):
        tree.focus_set()
    tree.bind('<Button-1>', on_click, add="+")

    # Funktionen
    def remove_selected():
        selected_items = tree.selection()
        for item in selected_items:
            tree.item(item, tags=('grayed',))
            tree.tag_configure('grayed', foreground='gray')
            grayed_indices.add(item)
        tree.selection_remove(selected_items)

    def restore_grayed_rows():
        for item in grayed_indices:
            tree.item(item, tags=())
        grayed_indices.clear()
        tree.tag_configure('grayed', foreground='black')
        auto_nan_checked.set(False)

    def remove_grayed_rows():
        nonlocal df
        indices_to_drop = []
        for item in grayed_indices:
            tree_values = tree.item(item, "values")
            index_in_df = int(tree_values[0])
            indices_to_drop.append(index_in_df)
        df = df.drop(index=indices_to_drop).reset_index(drop=True)
        filter_window.destroy()
        return df

    def auto_select_full_devices():
        tree.selection_remove(tree.selection())
        for item in tree.get_children():
            values = tree.item(item, "values")
            row_dict = dict(zip(['Index'] + list(df.columns), values))

            # String "nan" als NaN behandeln
            cell_values = [row_dict[col] for col in nan_relevant_cols]
            cell_values = [None if v == "nan" else v for v in cell_values]

            # Prüfen, ob alle vier Zellen einen Wert haben
            if all(v is not None for v in cell_values):
                tree.selection_add(item)

        remove_selected()



    def toggle_auto_nan_filter():
        if auto_nan_checked.get():
            auto_select_full_devices()
        else:
            restore_grayed_rows()

    # Button-UI
    button_frame = tk.Frame(filter_window)
    button_frame.pack(pady=5)

    remove_button = tk.Button(button_frame, text="Kick out", command=remove_selected)
    remove_button.pack()

    refresh_button = tk.Button(
        button_frame,
        text="Reset",
        command=restore_grayed_rows
    )
    refresh_button.pack()

    auto_nan_checkbox = tk.Checkbutton(
        button_frame,
        text="Kick out solar cells and show only halfstacks",
        variable=auto_nan_checked,
        command=toggle_auto_nan_filter
    )
    auto_nan_checkbox.pack()

    finish_button = tk.Button(button_frame, text="Done", command=remove_grayed_rows)
    finish_button.pack()

    filter_window.grab_set()
    filter_window.wait_window()
    return df
