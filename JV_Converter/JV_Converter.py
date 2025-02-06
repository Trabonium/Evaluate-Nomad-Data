import os
import shutil
import glob
import csv
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
from tkinter import ttk

def create_directory(path):
    if not os.path.exists(path):
        os.makedirs(path)

def move_mpp_files(path):
    newdirMPP = os.path.join(path, "MaxPowerPointTracking")
    create_directory(newdirMPP)
    
    for file in glob.iglob(os.path.join(path, "*MPP*")):
        dst = os.path.join(newdirMPP, os.path.basename(file))
        
        with open(file, 'r') as input_file:
            reader = csv.reader(input_file)
            lines = [line for line in reader]
        
        if lines and lines[0][0].startswith("SPP"):
            lines[0][0] = lines[0][0][4:]
        
        with open(file, 'w', newline='') as output_file:
            writer = csv.writer(output_file)
            writer.writerows(lines)

        
        if file.endswith("MPP.csv"):
            if ".px" in os.path.basename(file):
                os.rename(file, file[:-20] + ".csv")
                if ".mpp.csv" in os.path.basename(file):
                    pass
                else:
                    os.rename(file, file[:-4] + ".mpp.csv")
            else:
                pxnumber = file.split("_")[-4][2]
                os.rename(file, file[:-20] + f".px{pxnumber}.mpp.csv")

        if file.endswith("MPP_FULL.csv"):
            pass


        shutil.move(file, dst)
    messagebox.showinfo("Success", "Moved and updated MPP files.")

def move_soak_files(path, cycle_to_keep):
    newdirSoak = os.path.join(path, "Soak")
    create_directory(newdirSoak)
    
    for file in glob.iglob(os.path.join(path, f"*Cycle_[0-9]_illu*")):
        if f"Cycle_{cycle_to_keep}_illu" not in file:
            dst = os.path.join(newdirSoak, os.path.basename(file))
            shutil.move(file, dst)
    messagebox.showinfo("Success", "Moved Soak files.")

def rename_files(path, cycle_to_keep):
    rename_patterns = {
        f"*Cycle_{cycle_to_keep}_illu*": ".jv",
        "*_01_*": ".px1",
        "*_02_*": ".px2",
        "*_03_*": ".px3",
        "*_04_*": ".px4"
    }
    
    for pattern, replacement in rename_patterns.items():
        for file in glob.iglob(os.path.join(path, pattern)):
            basename_old = os.path.basename(file)
            new_name = os.path.join(path, basename_old.replace(pattern.split("*")[1], replacement))
            os.rename(file, new_name)
    messagebox.showinfo("Success", "Files renamed successfully.")

def browse_directory():
    path = filedialog.askdirectory(title="Select Directory")
    if path:
        entry_path.delete(0, tk.END)
        entry_path.insert(0, path)

def start_processing():
    path = entry_path.get()
    cycle_to_keep = entry_cycle.get()
    
    if not path or not os.path.exists(path):
        messagebox.showerror("Error", "Please select a valid directory.")
        return
    
    if not cycle_to_keep.isdigit() or not (0 <= int(cycle_to_keep) <= 9):
        messagebox.showerror("Error", "Enter a valid cycle number (0-9).")
        return
    
    confirmation = messagebox.askyesno("Confirmation", f"Apply renaming and sorting in:{path}\nKeeping Cycle: {cycle_to_keep}")
    if confirmation:
        move_mpp_files(path)
        move_soak_files(path, cycle_to_keep)
        rename_files(path, cycle_to_keep)
        messagebox.showinfo("Done", "All tasks completed successfully.")

# GUI Setup
root = tk.Tk()
root.title("Measurement File Organizer")
root.geometry("400x250")
root.resizable(False, False)

frame = ttk.Frame(root, padding=10)
frame.pack(fill=tk.BOTH, expand=True)

# Directory Selection
ttk.Label(frame, text="Select Directory:").grid(row=0, column=0, sticky="w")
entry_path = ttk.Entry(frame, width=40)
entry_path.grid(row=1, column=0, padx=5, pady=5)
ttk.Button(frame, text="Browse", command=browse_directory).grid(row=1, column=1, padx=5)

# Cycle Selection
ttk.Label(frame, text="Enter Cycle to Keep (0-9):").grid(row=2, column=0, sticky="w")
entry_cycle = ttk.Entry(frame, width=10)
entry_cycle.grid(row=3, column=0, padx=5, pady=5, sticky="w")

# Start Button
ttk.Button(frame, text="Start Renaming", command=start_processing).grid(row=4, column=0, columnspan=2, pady=10)

root.mainloop()
