import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
import math
import glob
from pathlib import Path

def _extract_wavelength_eqe_from_dataframe(df_file):
    """Try to extract wavelength and EQE arrays from a DataFrame.
    Handles common issues like comma decimals and EQE given as fraction or percent.
    Returns (wavelength_array, eqe_array) or (None, None) if extraction fails.
    """
    try:
        # Work on a copy
        tmp = df_file.copy()

        # Replace comma decimals in string columns before numeric conversion
        for col in [0, 1]:
            if col < tmp.shape[1]:
                try:
                    tmp.iloc[:, col] = tmp.iloc[:, col].astype(str).str.replace(',', '.').str.strip()
                except Exception:
                    pass

        col1_numeric = pd.to_numeric(tmp.iloc[:, 0], errors='coerce')
        col2_numeric = pd.to_numeric(tmp.iloc[:, 1], errors='coerce')

        valid_mask = ~(col1_numeric.isna() | col2_numeric.isna())
        wavelength_array = col1_numeric[valid_mask].values
        eqe_array = col2_numeric[valid_mask].values

        # Need at least a few points
        if len(wavelength_array) < 5 or len(eqe_array) < 5:
            return None, None

        mean_wl = np.nanmean(wavelength_array)
        mean_eqe = np.nanmean(np.abs(eqe_array))

        # Loose wavelength sanity check
        if not (150 <= mean_wl <= 2000):
            return None, None

        # EQE can be fraction (0-1) or percent (0-100). Decide scaling.
        if mean_eqe <= 1.5:
            # likely fraction -> convert to percent
            eqe_array = eqe_array * 100.0
        elif mean_eqe <= 200:
            # likely already percent -> keep as is
            pass
        else:
            # implausible EQE values
            return None, None

        return wavelength_array, eqe_array
    except Exception:
        return None, None

def plot_EQE_curves(result_df, file_column='filename'):

    max_EQE = 0.0
    wellenlenge_min = np.inf
    wellenlenge_max = 0.0
    
    # Keep track of successfully plotted files
    successful_plots = 0

    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Define custom color palette for specific groups
    custom_colors = {
        'A': '#001898',
        'B': '#006D94', 
        'Rob Ref': '#00876C',
        'C': '#33AD59',
        'E': '#66CB66',
        'D': '#AFE399',  # excluded group
        
        # ROB series colors
        'ROB_1': '#00876C',    # Rob Ref (same as Rob Ref)
        'ROB_2': '#A03E63',    # h30
        'ROB_3': '#DD85AB',    # h20
        'ROB_4': '#500D63',    # tQ
        'ROB_5': '#95409A',    # tQ (variant)
        'ROB_6': '#23003C',    # td
        'ROB_7': '#10E0C9',    # Q
        'ROB_8': '#3EFEDD',    # Q (variant)
        'ROB_9': '#00876C',    # Rob Ref (same as Rob Ref)
        'ROB_10': '#FFC548',   # P
        'ROB_11': '#FF9965',   # P (variant)
        'ROB_12': '#7E5F5E',   # A (variant)
        'ROB_13': '#947A72'    # A (variant)
    }
    
    # Function to determine group from filename
    def get_group_from_filename(filename):
        """Extract group identifier from filename"""
        basename = os.path.basename(filename).upper()
        
        # Check for specific ROB patterns first (ROB_1_, ROB_2_, etc.)
        import re
        rob_match = re.search(r'ROB_(\d+)_', basename)
        if rob_match:
            rob_number = int(rob_match.group(1))
            if 1 <= rob_number <= 13:
                return f'ROB_{rob_number}'
        
        # Check for other specific patterns in filename
        if 'ROB' in basename and not rob_match:
            return 'Rob Ref'
        elif 'REPA_' in basename:
            return 'A'
        elif 'REPB_' in basename:
            return 'B'
        elif 'REPC_' in basename:
            return 'C'
        elif 'REPD_' in basename:
            return 'D'
        elif 'REPE_' in basename:
            return 'E'
        else:
            # Default fallback - try to find single letter pattern
            match = re.search(r'[_\-\s]([ABCDE])[_\-\s\.]', basename)
            if match:
                return match.group(1)
            return 'A'  # Default to group A if no pattern found
    
    # Assign colors based on filename groups
    colors = []
    groups = []
    for _, row in result_df.iterrows():
        filepath = row.get('filename', '')
        group = get_group_from_filename(filepath)
        groups.append(group)
        colors.append(custom_colors.get(group, '#001898'))  # Default to A color if group not found
    
    # Show group assignments
    print(f"Group assignments:")
    for i, (group, color) in enumerate(zip(groups, colors)):
        filename = os.path.basename(result_df.iloc[i]['filename'])
        print(f"  {filename} → {group}")
    
    # iterate with an index for safe color indexing
    for file_idx, (index, row) in enumerate(result_df.iterrows()):
        try:
            # Get filepath
            filepath = row.get(file_column, None) if hasattr(row, "get") else row[file_column]
            if filepath is None or (isinstance(filepath, float) and pd.isna(filepath)):
                filepath = row.get('sample_id', row.get('maximum_efficiency_id', None))
            if filepath is None:
                continue

            print(f"Processing: {os.path.basename(filepath)}")
            
            if not os.path.exists(filepath):
                print(f"  File not found: {filepath}")
                continue

            success = False
            
            # Try different separators and approaches
            separators = ['\t', ',', ' ', ';']
            encodings = ['utf-8', 'latin-1', 'cp1252']
            
            for encoding in encodings:
                if success:
                    break
                for separator in separators:
                    if success:
                        break
                    
                    # Approach 1: Header at line 5 (as originally intended)
                    try:
                        df_file = pd.read_csv(filepath, sep=separator, header=4, encoding=encoding, on_bad_lines='skip')
                        wl, eq = _extract_wavelength_eqe_from_dataframe(df_file)
                        if wl is not None:
                            wavelength_array = wl
                            eqe_array = eq
                            success = True
                            print(f"  ✓ Parsed successfully")
                            break
                    except Exception:
                        pass
                    
                    # Approach 2: Try different header rows
                    if not success:
                        for header_row in [0, 1, 2, 3, 5, 6]:
                            try:
                                df_file = pd.read_csv(filepath, sep=separator, header=header_row, encoding=encoding, on_bad_lines='skip')
                                wl, eq = _extract_wavelength_eqe_from_dataframe(df_file)
                                if wl is not None:
                                    wavelength_array = wl
                                    eqe_array = eq
                                    success = True
                                    print(f"  ✓ Parsed successfully")
                                    break
                            except Exception:
                                continue
                    
                    # Approach 3: No header, try to find data section
                    if not success:
                        try:
                            df_file = pd.read_csv(filepath, sep=separator, header=None, encoding=encoding, on_bad_lines='skip')
                            # Try different starting rows to skip metadata
                            for skip_rows in range(min(10, len(df_file))):
                                try:
                                    data_part = df_file.iloc[skip_rows:]
                                    wl, eq = _extract_wavelength_eqe_from_dataframe(data_part)
                                    if wl is not None:
                                        wavelength_array = wl
                                        eqe_array = eq
                                        success = True
                                        print(f"  ✓ Parsed successfully")
                                        break
                                except Exception:
                                    continue
                                if success:
                                    break
                        except Exception:
                            pass
            
            if not success:
                print(f"  Failed to read file: {filepath}")
                continue

            # Try to extract JSC from line 2 (optional)
            jsc_value = None
            try:
                # Read first few lines to extract JSC
                with open(filepath, 'r', encoding='utf-8') as f:
                    lines = [f.readline().strip() for _ in range(3)]
                if len(lines) >= 2:
                    # Try to parse line 2 for JSC (common formats: tab-separated or space-separated)
                    line2_parts = lines[1].split('\t') if '\t' in lines[1] else lines[1].split()
                    if len(line2_parts) >= 2:
                        try:
                            # Try second column first, then third
                            for col_idx in [1, 2]:
                                if col_idx < len(line2_parts):
                                    potential_jsc = line2_parts[col_idx].replace(',', '.')
                                    jsc_value = float(potential_jsc)
                                    if 0 <= abs(jsc_value) <= 50:  # Reasonable JSC range (mA/cm²)
                                        break
                        except ValueError:
                            pass
            except Exception:
                pass

            # Update min/max trackers with actual data
            if len(eqe_array) > 0 and len(wavelength_array) > 0:
                current_max_eqe = np.max(eqe_array)
                current_min_wl = np.min(wavelength_array)
                current_max_wl = np.max(wavelength_array)
                
                if current_max_eqe > max_EQE:
                    max_EQE = current_max_eqe
                if current_min_wl < wellenlenge_min:
                    wellenlenge_min = current_min_wl
                if current_max_wl > wellenlenge_max:
                    wellenlenge_max = current_max_wl

                # Create label from filename, group, and JSC (if available)
                base_label = os.path.basename(filepath)
                group = groups[file_idx]
                
                if jsc_value is not None:
                    label = f"{base_label} [{group}] (JSC: {jsc_value:.1f})"
                else:
                    label = f"{base_label} [{group}]"
                
                # Plot the data with custom group color
                ax.plot(wavelength_array, eqe_array, color=colors[file_idx], label=label, linewidth=2)
                successful_plots += 1
                print(f"  ✓ Plotted {len(wavelength_array)} points")
            else:
                print(f"  ✗ No valid data found")

        except Exception as e:
            print(f"  Error processing file {filepath}: {e}")
            continue

    print(f"\nSuccessfully plotted {successful_plots} out of {len(result_df)} files")
    
    # Set reasonable defaults if no data was found
    if successful_plots == 0:
        print("No data was successfully plotted!")
        max_EQE = 100
        wellenlenge_min = 300
        wellenlenge_max = 850
    
    # Plot settings
    if max_EQE > 0:
        yticks = [i for i in range(0, int(math.ceil(max_EQE/10)*10+10), 10)]
    else:
        yticks = [0, 20, 40, 60, 80, 100]
    
    ax.set_yticks(yticks)
    ax.set_ylim(0, max(yticks))
    
    if successful_plots > 0:
        ax.legend()
    
    # Set x-axis limits with some padding
    if wellenlenge_min != np.inf and wellenlenge_max > 0:
        ax.set_xlim(wellenlenge_min-0, wellenlenge_max+0)
    else:
        ax.set_xlim(300, 1000)
    
    ax.set_title(f'EQE Curves ({successful_plots} files)')
    ax.set_xlabel('Wavelength (nm)')
    if mpl.rcParams.get("text.usetex", False):
        ax.set_ylabel(r'EQE (\%)')
    else:
        ax.set_ylabel('EQE (%)')

    # Axis ticks and borders
    ax.tick_params(axis='both', which='both', direction='in', width=2, bottom=1, top=1, left=1, right=1)
    
    ax.spines['top'].set_linewidth(2)
    ax.spines['bottom'].set_linewidth(2)
    ax.spines['left'].set_linewidth(2)
    ax.spines['right'].set_linewidth(2)

    # Zero lines
    ax.axhline(y=0, color='black', linewidth=0.5)
    ax.axvline(x=0, color='black', linewidth=0.5)
    
    return fig


def get_eqe_files_from_folder(folder_path, file_extensions=None):
    """Get all EQE files from a folder"""
    if file_extensions is None:
        file_extensions = ['*.txt', '*.eqe', '*.csv', '*.dat']
    
    folder_path = Path(folder_path)
    if not folder_path.exists():
        print(f"Folder not found: {folder_path}")
        return []
    
    all_files = []
    for ext in file_extensions:
        all_files.extend(folder_path.glob(ext))
    
    file_paths = sorted([str(f) for f in all_files])
    print(f"Found {len(file_paths)} EQE files")
    return file_paths


# =============================================================================
# MAIN SCRIPT - Define variables and run the function
# =============================================================================

if __name__ == "__main__":
    
    # Specify folder path - will automatically find all EQE files
    folder_path_core = r"\\129.13.79.200\AG_Lemmer$\Forschungsprojekte\Spektroskopie\Perovskite solar cells\Data\SonSim\Daniel\GQ2025Rep_Rob\EQE"
    folder_path_specific = r"\Median\onlyRob"
    folder_path = folder_path_core + folder_path_specific

    # Get all EQE files from the folder
    file_names = get_eqe_files_from_folder(folder_path)
    
    if len(file_names) == 0:
        print(f"No EQE files found in folder: {folder_path}")
        print("Please check the folder path and make sure it contains .txt, .eqe, .csv, or .dat files")
        exit()
    
    print(f"Processing {len(file_names)} files...")
    
    # Create simple DataFrame with just filenames
    results_df = pd.DataFrame({'filename': file_names})
    
    print("=== EQE Plot Generator ===")
    print(f"Folder: {folder_path}")
    print(f"Number of files found: {len(file_names)}")
    print("\nFiles to be plotted:")
    for i, file in enumerate(file_names):
        print(f"  {i+1:2d}. {os.path.basename(file)}")
    
    print(f"\nProcessing files...")
    
    try:
        # Call the plotting function
        fig = plot_EQE_curves(results_df)
        
        # Show the plot
        plt.tight_layout()
        plt.show()
        
        print("\nPlot displayed successfully!")
        
    except FileNotFoundError as e:
        print(f"Error: Could not find one or more EQE data files.")
        print(f"Error details: {e}")
        
    except Exception as e:
        print(f"An error occurred while creating the plot: {e}")
        print("Please check your EQE data files and file paths.")


# =============================================================================
# USAGE: 
# 1. Set folder_path to your EQE data folder
# 2. Run: python eqe_plot_runner.py
# 
# Supports: .txt, .eqe, .csv, .dat files
# Auto-detects file format and assigns colors based on filename patterns
# =============================================================================