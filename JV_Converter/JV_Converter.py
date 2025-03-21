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

def show_auto_close_message(title, message, timeout=3000):
    msg_window = tk.Toplevel(root)  # Attach to main window
    msg_window.title(title)
    msg_window.geometry("300x100")

    label = ttk.Label(msg_window, text=message, wraplength=280)
    label.pack(expand=True, padx=10, pady=10)

    msg_window.after(timeout, msg_window.destroy)  # Auto close after timeout
    root.update_idletasks()  # Update GUI without blocking execution


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

        shutil.move(file, dst)
        
        if dst.endswith("MPP.csv"):
            if ".px" in os.path.basename(dst):
                new_dst = dst[:-20] + ".csv"
                os.rename(dst, new_dst)
                dst = new_dst
                if ".mpp.csv" in os.path.basename(dst):
                    pass
                else:
                    os.rename(dst, dst[:-4] + ".mpp.csv")
            else:
                pxnumber = dst.split("_")[-4][2]
                os.rename(dst, dst[:-20] + f".px{pxnumber}.mpp.csv")

    show_auto_close_message("Success", "Moved and updated MPP files.", 2000)

def move_soak_files(path, cycle_to_keep, preserve_cycle):
    newdirSoak = os.path.join(path, "Soak")
    create_directory(newdirSoak)
    
    for file in glob.iglob(os.path.join(path, f"*Cycle_[0-9]_illu*")):
        if not preserve_cycle and f"Cycle_{cycle_to_keep}_illu" not in file:
            dst = os.path.join(newdirSoak, os.path.basename(file))
            shutil.move(file, dst)
        #Add preserve cycle fuction with "_" after .px
    show_auto_close_message("Success", "Moved Soak files.", 2000)

def rename_files(path, cycle_to_keep, preserve_cycle):
    rename_patterns = {
        "_01_": ".px1",
        "_02_": ".px2",
        "_03_": ".px3",
        "_04_": ".px4"
    }

    if preserve_cycle:
        # Process all cycles instead of a specific one
        cycle_pattern = "*Cycle_*_illu*.csv"
    else:
        cycle_pattern = f"*Cycle_{cycle_to_keep}_illu*.csv"

    for file in glob.iglob(os.path.join(path, cycle_pattern)):
        basename_old = os.path.basename(file)
        new_name = basename_old.replace("_illu", "")  # Remove "_illu"

        # Insert .jv before .csv
        if new_name.endswith(".csv"):
            new_name = new_name[:-4] + ".jv.csv"

        # Apply renaming patterns for pixel numbers
        for pattern, replacement in rename_patterns.items():
            if pattern in new_name:
                new_name = new_name.replace(pattern, replacement)

        new_file_path = os.path.join(path, new_name)
        os.rename(file, new_file_path)

    show_auto_close_message("Success", "Files renamed successfully.", 2000)




def browse_directory():
    path = filedialog.askdirectory(title="Select Directory")
    if path:
        entry_path.delete(0, tk.END)
        entry_path.insert(0, path)

def start_processing():
    path = entry_path.get()
    cycle_to_keep = entry_cycle.get()
    preserve_cycle = preserve_cycle_var.get()
    
    if not path or not os.path.exists(path):
        messagebox.showerror("Error", "Please select a valid directory.")
        return
    
    if not cycle_to_keep.isdigit() or not (0 <= int(cycle_to_keep) <= 9):
        messagebox.showerror("Error", "Enter a valid cycle number (0-9).")
        return
    
    confirmation = messagebox.askyesno("Confirmation", f"Apply renaming and sorting in:\n{path}\nKeeping Cycle: {cycle_to_keep}\nPreserve cycle info: {preserve_cycle}")
    if confirmation:
        move_mpp_files(path)
        move_soak_files(path, cycle_to_keep, preserve_cycle)
        rename_files(path, cycle_to_keep, preserve_cycle)
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

# Preserve Cycle Checkbox
preserve_cycle_var = tk.BooleanVar()
ttk.Checkbutton(frame, text="Preserve cycle information", variable=preserve_cycle_var).grid(row=4, column=0, sticky="w", pady=5)

# Start Button
ttk.Button(frame, text="Start Renaming", command=start_processing).grid(row=5, column=0, columnspan=2, pady=10)

root.mainloop()
