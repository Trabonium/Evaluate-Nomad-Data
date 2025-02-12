import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
import numpy as np
import pandas as pd
import seaborn as sns
import math
from functions.api_calls_get_data import get_specific_data_of_sample

### Function to plot JV curves ###______________________________________________________________________________________________________

def plot_JV_curves(result_df, curve_type, nomad_url, token):
    fig, ax = plt.subplots()
    
    # Define a color palette for the groups
    colors = plt.cm.viridis(np.linspace(0, 0.95, len(result_df['category'].unique())))
    
    # Set the color cycle for the axes
    ax.set_prop_cycle(color=colors)
    PCE = None
    for index, row in result_df.iterrows():
        jv_data = get_specific_data_of_sample(row[f'{curve_type}_id'], "JVmeasurement", nomad_url, token)
        for cell in jv_data:
            for i in range(2):
                PCE = cell["jv_curve"][i]["efficiency"]
                if cell["jv_curve"][i]["efficiency"] == row[f'{curve_type}'] and \
                   (curve_type == 'maximum_efficiency' or curve_type == 'closest_median'):
                        ax.plot(cell["jv_curve"][i]["voltage"], \
                                 cell["jv_curve"][i]["current_density"], \
                                 label=f"{row['category']}: {round(PCE,2)}%")
                        print(cell["name"])
                        break

    # Plot settings
    ax.legend()
    ax.set_xlim(-0.2, 1.3)
    ax.set_ylim(-5, 25)
    ax.set_title(f'{curve_type.capitalize()} JV Curves', fontsize=16)
    ax.set_xlabel('Voltage (V)', fontsize=12)
    ax.set_ylabel('Current Density(mA/cm²)', fontsize=12)

    # Axis ticks and borders
    ax.tick_params(axis='both', which='both', direction='in', width=2, bottom=1, top=1, left=1, right=1)
    ax.tick_params(labelsize=12)
    ax.spines['top'].set_linewidth(2)
    ax.spines['bottom'].set_linewidth(2)
    ax.spines['left'].set_linewidth(2)
    ax.spines['right'].set_linewidth(2)

    # Zero lines
    ax.axhline(y=0, color='black', linewidth=0.5)
    ax.axvline(x=0, color='black', linewidth=0.5)
    
    #fig.savefig(f"{curve_type}.png", dpi=300, transparent=True, bbox_inches='tight')

    return fig

### Function to plot EQE curves ###_____________________________________________________________________________________________________

def plot_EQE_curves(df, result_df, nomad_url, token):
    max_EQE = .0
    wellenlenge_min = np.inf
    wellenlenge_max = .0

    fig, ax = plt.subplots()
    
    # Define a color palette for the groups
    colors = plt.cm.viridis(np.linspace(0, 0.95, len(result_df['category'].unique())))
    
    # Set the color cycle for the axes
    ax.set_prop_cycle(color=colors)
    
    for index, row in result_df.iterrows():
        try:
            # Data from server
            eqe_data = get_specific_data_of_sample(row[f'maximum_efficiency_id'], 'EQEmeasurement', nomad_url, token)
            # See if data is returned
            eqe_data[0]
        except IndexError:
            # Sort df by maximum efficiency and try again
            variation = row['category']
            sorted_df = df[df['variation'] == variation].sort_values(by='efficiency', ascending=False)
            for _, sorted_row in sorted_df.iterrows():
                try:
                    eqe_data = get_specific_data_of_sample(sorted_row[f'sample_id'], 'EQEmeasurement', nomad_url, token)
                    eqe_data[0]
                    break
                except IndexError:
                    continue
            else:
                # If no valid data is found, skip this row
                continue
        
        #Relevant arrays
        wavelength_array = eqe_data[0]['eqe_data'][0]['wavelength_array']
        eqe_array = [w * 100 for w in eqe_data[0]['eqe_data'][0]['eqe_array']]
        if max_EQE < max(eqe_array):
            max_EQE = max(eqe_array)
        if wellenlenge_min > min(wavelength_array):
            wellenlenge_min = min(wavelength_array)
        if wellenlenge_max < max(wavelength_array):
            wellenlenge_max = max(wavelength_array)
        ax.plot(wavelength_array, eqe_array, color=colors[index], label=f"{row['category']}: {round(eqe_data[0]['eqe_data'][0]['integrated_jsc'],2)} mA/cm² {round(eqe_data[0]['eqe_data'][0]['bandgap_eqe'],2)} eV")
        print(row[f'maximum_efficiency_id'])
                        
    # Plot settings
    yticks = [i for i in range(0,math.ceil(max_EQE/10)*10+10,10)] #erstellt eine liste von 0 bis max EQE bis auf 10 aufgerundet in 10er schritten
    ax.set_yticks(yticks)
    ax.set_ylim(0, max(yticks))
    ax.legend()
    ax.set_xlim(wellenlenge_min-20, wellenlenge_max+20)
    ax.set_title(f'EQE Curves', fontsize=16)
    ax.set_xlabel('Wavelength (nm)', fontsize=12)
    ax.set_ylabel('EQE (%)', fontsize=12)

    # Axis ticks and borders
    ax.tick_params(axis='both', which='both', direction='in', width=2, bottom=1, top=1, left=1, right=1)
    ax.tick_params(labelsize=12)
    ax.spines['top'].set_linewidth(2)
    ax.spines['bottom'].set_linewidth(2)
    ax.spines['left'].set_linewidth(2)
    ax.spines['right'].set_linewidth(2)

    # Zero lines
    ax.axhline(y=0, color='black', linewidth=0.5)
    ax.axvline(x=0, color='black', linewidth=0.5)
    
    #fig.savefig(f"{curve_type}.png", dpi=300, transparent=True, bbox_inches='tight')

    return fig
    

### Function to plot MPP curves ###_____________________________________________________________________________________________________

def plot_MPP_curves(df, result_df, nomad_url, token):
    
    fig, ax = plt.subplots()
    
    # Define a color palette for the groups
    colors = plt.cm.viridis(np.linspace(0, 0.95, len(result_df['category'].unique())))
    
    # Set the color cycle for the axes
    ax.set_prop_cycle(color=colors)
    
    for index, row in result_df.iterrows():
        #Data from server
        try:
            # Data from server
            mpp_data = get_specific_data_of_sample(row[f'maximum_efficiency_id'],'MPPTracking', nomad_url, token)            # See if data is returned
            mpp_data[0]
        except IndexError:
            # Sort df by maximum efficiency and try again
            variation = row['category']
            sorted_df = df[df['variation'] == variation].sort_values(by='efficiency', ascending=False)
            for _, sorted_row in sorted_df.iterrows():
                try:
                    mpp_data = get_specific_data_of_sample(sorted_row[f'sample_id'], 'MPPTracking', nomad_url, token)
                    mpp_data[0]
                    break
                except IndexError:
                    continue
            else:
                # If no valid data is found, skip this row
                continue

        #Relevant arrays
        time_array = mpp_data[0]['time']
        pce_array = mpp_data[0]['efficiency']
        voltage_array = mpp_data[0]['voltage']
        last_pce = mpp_data[0]['properties']['last_pce']
        #Plot
        ax.plot(time_array, pce_array, label=f"{row['category']}", color=colors[index])
        print(row[f'maximum_efficiency_id'])
                        
 
    # Plot settings
    ax.legend()
    ax.set_xlim(0, 300)
    ax.set_ylim(0, 25)
    ax.set_title(f'MPP Tracking', fontsize=16)
    ax.set_xlabel('Time (s)', fontsize=12)
    ax.set_ylabel('PCE (%)', fontsize=12)

    # Axis ticks and borders
    ax.tick_params(axis='both', which='both', direction='in', width=2, bottom=1, top=1, left=1, right=1)
    ax.tick_params(labelsize=12)
    ax.spines['top'].set_linewidth(2)
    ax.spines['bottom'].set_linewidth(2)
    ax.spines['left'].set_linewidth(2)
    ax.spines['right'].set_linewidth(2)

    # Zero lines
    ax.axhline(y=0, color='black', linewidth=0.5)
    ax.axvline(x=0, color='black', linewidth=0.5)
    
    #fig.savefig(f"{curve_type}.png", dpi=300, transparent=True, bbox_inches='tight')

    return fig


### Function to plot box and scatter plots ###_________________________________________________________________________________________

def plot_box_and_scatter(df, quantity, SeparateScanDir=False):
    # Define the base color palette for unique variations
    base_colors = plt.cm.viridis(np.linspace(0, 0.95, len(df[quantity].unique())))

    if SeparateScanDir:
        # Extend the colors for 'forward' groups by shifting brightness
        bw_colors = base_colors
        fw_colors = fw_colors = [(color[0], color[1], color[2], 0.5) for color in base_colors]

        # Combine backwards and forwards colors interleaved
        colors = []
        for bw_color, fw_color in zip(bw_colors, fw_colors):
            colors.append(bw_color)  # Backward color
            colors.append(fw_color)  # Forward color
    else:
        # Use only the base color palette
        colors = base_colors

    # Sort the unique variation groups first to ensure consistent order
    sorted_variations = sorted(df[quantity].unique())
    if SeparateScanDir:
        sorted_groups = [
            f"{group}_bw" if i % 2 == 0 else f"{group}_fw"
            for group in sorted_variations
            for i in range(2)
        ]
    else:
        sorted_groups = sorted_variations

    # Define Y-Axis Labels
    jv_quantity = ['efficiency', 'open_circuit_voltage', 'fill_factor', 'short_circuit_current_density']
    
    jv_quantity_labels = {
        'open_circuit_voltage': r"$V_{oc} \, (V)$",
        'fill_factor': "FF (%)",
        'efficiency': "PCE (%)",
        'short_circuit_current_density': r"$J_{sc} \, (mA/cm²)$"
    }

    fig, axes = plt.subplots(2, 2, figsize=(15, 10))  # 2x2 grid of subplots
    axes = axes.flatten()  # Flatten to make indexing easier
    
    positions = [i + 1 for i in range(len(sorted_groups))]  # Define positions for each group

    for i, ax in enumerate(axes):

        # Draw the box plot without fliers and with colors
        medianprops = dict(color='red')
        for j, (group, color) in enumerate(zip(sorted_groups, colors)):
            if SeparateScanDir:
                # Separate data into backward and forward scan directions
                if group.endswith("_bw"):
                    base_group = group[:-3]  # Remove "_bw" suffix
                    group_data = df[
                        (df[quantity] == base_group) & 
                        (df['scan_direction'] == 'backwards')
                    ][jv_quantity[i]].dropna()
                    # Apply shift to the left for backward scans
                    group_position = positions[j]/2 + 0.3
                elif group.endswith("_fw"):
                    base_group = group[:-3]  # Remove "_fw" suffix
                    group_data = df[
                        (df[quantity] == base_group) & 
                        (df['scan_direction'] == 'forwards')
                    ][jv_quantity[i]].dropna()
                    # Apply shift to the right for forward scans
                    group_position = positions[j]/2 + 0.2
            else:
                # Group data by variation only
                group_data = df[df[quantity] == group][jv_quantity[i]].dropna()
                group_position = positions[j]

            # Plot the boxplot
            ax.boxplot(group_data, positions=[group_position], showmeans=False, showfliers=False, widths=0.4, patch_artist=True,
                       boxprops=dict(facecolor=color, color='black'),
                       medianprops=medianprops)

        # Overlay the scatter plot with black points
        for j, group in enumerate(sorted_groups):
            if SeparateScanDir:
                # Separate data into backward and forward scan directions
                if group.endswith("_bw"):
                    base_group = group[:-3]  # Remove "_bw" suffix
                    group_data = df[
                        (df[quantity] == base_group) & 
                        (df['scan_direction'] == 'backwards')
                    ][jv_quantity[i]].dropna()
                    # Apply shift to the left for backward scans
                    group_position = positions[j]/2 + 0.3
                elif group.endswith("_fw"):
                    base_group = group[:-3]  # Remove "_fw" suffix
                    group_data = df[
                        (df[quantity] == base_group) & 
                        (df['scan_direction'] == 'forwards')
                    ][jv_quantity[i]].dropna()
                    # Apply shift to the right for forward scans
                    group_position = positions[j]/2 + 0.2
            else:
                # Group data by variation only
                group_data = df[df[quantity] == group][jv_quantity[i]].dropna()
                group_position = positions[j]

            # Add jitter to x positions
            jittered_x = np.random.normal(loc=group_position, scale=0.05, size=len(group_data))
            ax.scatter(jittered_x, group_data, color='black', alpha=0.9, zorder=2, s=25)

        # Axis label and Ticks
        ax.set_ylabel(f"{jv_quantity_labels[jv_quantity[i]]}", size=16)
        ax.set_xticks([i + 1 for i in range(len(sorted_variations))])
        ax.set_xticklabels(sorted_variations, size=14, rotation=45 if len(sorted_variations) > 4 else 0, ha='right' if len(sorted_variations) > 4 else 'center')
        ax.yaxis.set_major_locator(MaxNLocator(nbins=6, steps=[1, 2, 5, 10])) 
        ax.tick_params(axis='both', labelsize=14)
        ax.grid(axis='y', color='grey', linestyle='--', linewidth=0.5, alpha=0.5) 

        # Border line and Ticks Formatting
        ax.spines['top'].set_visible(True)
        ax.spines['right'].set_visible(True)
        ax.spines['bottom'].set_linewidth(2)
        ax.spines['left'].set_linewidth(2)
        ax.spines['top'].set_linewidth(2)
        ax.spines['right'].set_linewidth(2)
        ax.tick_params(axis='both', right=True, top=True, direction='in', width=2, colors='black', length=5)

        # Transparent Background
        fig.patch.set_facecolor('none')
        ax.patch.set_facecolor('none')

    # Adjust layout to prevent overlap
    plt.tight_layout()
    
    return fig