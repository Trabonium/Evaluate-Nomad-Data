import os
import tkinter as tk
from tkinter import filedialog

def add_prefix_to_files(folder_path, prefix="DaBa_"):
    for filename in os.listdir(folder_path):
        old_path = os.path.join(folder_path, filename)
        if os.path.isfile(old_path):  # Ensure it's a file, not a folder
            new_path = os.path.join(folder_path, prefix + filename)
            os.rename(old_path, new_path)
    print("Renaming completed.")

def select_folder():
    root = tk.Tk()
    root.withdraw()  # Hide the root window
    folder_path = filedialog.askdirectory(title="Select Folder")
    
    if folder_path:  # If a folder is selected
        add_prefix_to_files(folder_path)
    else:
        print("No folder selected. Exiting.")

select_folder()
