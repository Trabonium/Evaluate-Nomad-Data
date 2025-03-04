import tkinter as tk
from tkinter import ttk
import pandas as pd

def freier_filter(df, master):
    filter_window = tk.Toplevel(master)
    filter_window.title("Datenansicht")
    filter_window.geometry("600x400")
    
    grayed_indices = set()

    def remove_selected():
        selected_items = tree.selection()
        for item in selected_items:
            df_index = int(tree.item(item, "values")[0])
            tree.item(item, tags=('grayed',))
            tree.tag_configure('grayed', foreground='gray')
            grayed_indices.add(df_index)
        tree.selection_remove(selected_items)

    def restore_grayed_rows():
        for item in tree.get_children():
            tree.item(item, tags=())  # Entfernt das 'grayed' Tag
        grayed_indices.clear()

    def remove_grayed_rows():
        nonlocal df
        df = df.drop(grayed_indices).reset_index(drop=True)
        filter_window.destroy()
        return df

    frame = tk.Frame(filter_window)
    frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

    tree = ttk.Treeview(frame, columns=['Index'] + list(df.columns), show='headings', selectmode='extended')
    tree.heading('Index', text='Index')
    tree.column('Index', width=50)

    for col in df.columns:
        tree.heading(col, text=col)
        tree.column(col, width=100)

    for i, row in df.iterrows():
        tree.insert("", tk.END, values=[i] + list(row))

    tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    scrollbar = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    tree.configure(yscroll=scrollbar.set)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    button_frame = tk.Frame(filter_window)
    button_frame.pack(pady=5)

    remove_button = tk.Button(button_frame, text="Ausgegraute Zeilen markieren", command=remove_selected)
    remove_button.pack()
    
    refresh_button = tk.Button(button_frame, text="Reset", command=restore_grayed_rows)
    refresh_button.pack()

    finish_button = tk.Button(button_frame, text="Fertig", command=remove_grayed_rows)
    finish_button.pack()

    tree.configure(selectmode='extended')  # Aktiviert Mehrfachauswahl mit Shift und Pfeiltasten
    tree.bind("<Shift-Up>", lambda e: tree.selection_add(tree.focus()))
    tree.bind("<Shift-Down>", lambda e: tree.selection_add(tree.focus()))
    
    filter_window.grab_set()
    filter_window.wait_window()
    return df