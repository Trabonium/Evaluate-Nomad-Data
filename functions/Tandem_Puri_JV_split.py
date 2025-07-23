import os
import tkinter as tk
from tkinter import filedialog, messagebox
import re
import csv
from datetime import datetime

def tandem_puri_jv_split(master):
    def parse_sample_blocks(lines):
        blocks = []
        block = []
        for line in lines:
            if line.startswith("Time(s):"):
                if block:
                    blocks.append(block)
                block = [line]
            elif block:
                block.append(line)
        if block:
            blocks.append(block)
        return blocks

    def extract_metadata(header_lines):
        metadata = {}
        for line in header_lines:
            if ":" in line:
                key, value = line.split(":", 1)
                metadata[key.strip()] = value.strip()
        return metadata

    def format_old_file(sample_name, area, is_illuminated, date, scan1, scan2):
        header = [
            f"LTI @ KIT\tPV cell J-V measurement\t\t",
            f"Cell ID:\t{sample_name}\t\t",
            f"Cell area [cm²]:\t{area}\t\t",
            f"Cell illuminated\t{int(is_illuminated)}\t\t",
            f"{date}\t\t",
            f"Jsc [mA/cm²]:\t0.000000E+0\t0.000000E+0\t",
            f"Voc [V]:\t0.000000E+0\t0.000000E+0\t",
            "Fill factor:\t0.000000E+0\t0.000000E+0\t",
            "Efficiency:\t0.000000E+0\t0.000000E+0\t",
            "Commentary:\t\t\t",
            "Hysteresis\t1\t\t",
            "Voltage [V]\tCurrent density [1] [mA/cm^2]\tCurrent density [2] [mA/cm^2]\tAverage current density [mA/cm^2]"
        ]
        
        data_lines = []
        for (v1, j1), (v2, j2) in zip(scan1, reversed(scan2)):
            avg = (j1 + j2) / 2
            data_lines.append(f"{v1:.6E}\t{j1:.6E}\t{j2:.6E}\t{avg:.6E}")
        return "\n".join(header + data_lines)

    def process_file(file_path, output_folder):
        with open(file_path, 'r', encoding='latin-1') as f:
            lines = [line.strip() for line in f if line.strip()]
        
        header_lines = []
        for i, line in enumerate(lines):
            if line.startswith("Time(s):"):
                break
            header_lines.append(line)
        
        metadata = extract_metadata(header_lines)
        sample_name = metadata.get("Sample Name", "unknown_sample")
        area = metadata.get("Active Area (cm2)", "1.0")
        date = metadata.get("Test Start Time", "20000000_00:00:00")
        date = datetime.strptime(date, "%Y%m%d_%H:%M:%S").strftime("%Y-%m-%d\t%H:%M:%S")
        is_illuminated = float(metadata.get("Illumination Intensity (mW/cm2)", "0")) > 0

        blocks = parse_sample_blocks(lines[i:])
        for idx in range(0, len(blocks), 2):
            try:
                forward_lines = blocks[idx]
                reverse_lines = blocks[idx + 1]
            except IndexError:
                continue

            def parse_scan(scan_lines):
                data_start = scan_lines.index(next(line for line in scan_lines if line.startswith("Voltage")))
                data = scan_lines[data_start + 1:]
                return [(float(v), float(j)) for v, j in (row.split(",") for row in data)]

            forward = parse_scan(forward_lines)
            reverse = parse_scan(reverse_lines)

            scan_index = idx // 2 + 1
            filename = f"{sample_name}_px{scan_index}.jv.csv"
            output_path = os.path.join(output_folder, filename)

            content = format_old_file(sample_name, area, is_illuminated, date, forward, reverse)
            with open(output_path, 'w', encoding='utf-8') as out_file:
                out_file.write(content)

    def run_conversion():
        input_folder = filedialog.askdirectory(title="Select Folder with _ivraw.csv files", parent=window)
        if not input_folder:
            return
        
        output_folder = os.path.join(input_folder, "converted")
        os.makedirs(output_folder, exist_ok=True)

        processed = 0
        for filename in os.listdir(input_folder):
            if filename.lower().endswith("_ivraw.csv"):
                process_file(os.path.join(input_folder, filename), output_folder)
                processed += 1
                
        messagebox.showinfo("Done", f"Processed {processed} files.\nOutput saved to:\n{output_folder}", parent=window)

    # --- GUI Setup in Toplevel ---
    window = tk.Toplevel(master)
    window.title("IV Converter")
    window.geometry("300x120")

    label = tk.Label(window, text="Convert _ivraw.csv files to old format", pady=10)
    label.pack()

    btn = tk.Button(window, text="Select Folder and Run", command=run_conversion)
    btn.pack(pady=10)

    #force to focus this window and not the main window
    window.grab_set()
    window.wait_window()
