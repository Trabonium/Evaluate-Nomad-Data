import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from functions.api_calls_get_data import get_specific_data_of_sample

### Function to plot JV curves ###______________________________________________________________________________________________________

def plot_JV_curves(result_df, curve_type, nomad_url, token):
    fig, ax = plt.subplots()
    
    # Define a color palette for the groups
    colors = plt.cm.viridis(np.linspace(0, 1, len(result_df)))
    
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

### Function to plot box and scatter plots ###_________________________________________________________________________________________

def plot_box_and_scatter(df, quantities,  SeparateScanDir=False):

    unique_variations = df['variation'].unique()

    # Daten filtern und organisieren
    filtered_data = [[], [], [], [], [], [], [], []] 

    for i, var in enumerate(unique_variations):
        filtered_data[0].append(df.loc[(df['scan_direction'] == 'backwards') & (df['variation'] == var), 'efficiency'].tolist())
        filtered_data[1].append(df.loc[(df['scan_direction'] == 'forwards') & (df['variation'] == var), 'efficiency'].tolist())
        filtered_data[2].append(df.loc[(df['scan_direction'] == 'backwards') & (df['variation'] == var), 'fill_factor'].tolist())
        filtered_data[3].append(df.loc[(df['scan_direction'] == 'forwards') & (df['variation'] == var), 'fill_factor'].tolist())
        filtered_data[4].append(df.loc[(df['scan_direction'] == 'backwards') & (df['variation'] == var), 'short_circuit_current_density'].tolist())
        filtered_data[5].append(df.loc[(df['scan_direction'] == 'forwards') & (df['variation'] == var), 'short_circuit_current_density'].tolist())
        filtered_data[6].append(df.loc[(df['scan_direction'] == 'backwards') & (df['variation'] == var), 'open_circuit_voltage'].tolist())
        filtered_data[7].append(df.loc[(df['scan_direction'] == 'forwards') & (df['variation'] == var), 'open_circuit_voltage'].tolist())

    # Subplot erstellen
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))  # Seitenverhältnis anpassen
    axes = axes.flatten()

    # Achsentitel
    yachsenname = ['PCE [%]', 'FF [%]', r'J$_{\text{sc}}$ [mA/cm$^2$]', r'V$_{\text{oc}}$ [V]']
    legendenboolean = True
    for i in range(0, 8, 2):
        data = []
        for k, (a, b) in enumerate(zip(filtered_data[i], filtered_data[i + 1])):
            data.extend([(unique_variations[k], value, 'reverse') for value in a])
            data.extend([(unique_variations[k], value, 'forwards') for value in b])

        dataframe = pd.DataFrame(data, columns=['Gruppe', 'Wert', 'Richtung'])

        ax = axes[int(i / 2)]
        sns.boxplot(x='Gruppe', y='Wert', hue='Richtung', data=dataframe, ax=ax, legend = legendenboolean)
        sns.stripplot(x='Gruppe', y='Wert', hue='Richtung', data=dataframe, dodge=True, jitter=True,
                      palette='dark:black', alpha=0.5, legend=False, ax=ax)
        legendenboolean = False
        # Achsentitel und Anpassungen
        ax.set_ylabel(yachsenname[int(i / 2)], fontsize=18, labelpad=10)
        ax.set_xticks(range(len(unique_variations)))
        ax.set_xticklabels(unique_variations, fontsize=14)
        ax.set_xlabel("")
        ax.tick_params(axis='y', labelsize=14)
        ax.grid(axis='y', linestyle='--', alpha=0.6)

    # Legende nur für den ersten Subplot
    handles, labels = axes[0].get_legend_handles_labels()
    axes[0].legend(handles, labels, loc='upper right', fontsize=12)

    plt.tight_layout()
    return fig

    '''
    # Define the base color palette for unique variations
    base_colors = plt.cm.viridis(np.linspace(0, 0.95, len(df['variation'].unique())))

    if SeparateScanDir:
        # Extend the colors for 'forward' groups by shifting brightness
        bw_colors = base_colors
        fw_colors = [plt.cm.viridis(min(1, color[0] + 0.0001)) for color in base_colors]

        # Combine backwards and forwards colors interleaved
        colors = []
        for bw_color, fw_color in zip(bw_colors, fw_colors):
            colors.append(bw_color)  # Backward color
            colors.append(fw_color)  # Forward color
    else:
        # Use only the base color palette
        colors = base_colors
    
    # Define Y-Axis Labels
    quantity_labels = {
        'open_circuit_voltage': 'Open Circuit Voltage (V)',
        'fill_factor': 'Fill Factor (%)',
        'efficiency': 'Efficiency (%)',
        'short_circuit_current_density': 'Short Circuit Current Density (mA/cm²)'
    }

    fig, ax = plt.subplots(figsize=(10, 5))

    # Sort the unique variation groups first to ensure consistent order
    # Define grouping logic based on the SeparateScanDir flag
    if SeparateScanDir:
        sorted_variations = sorted(df['variation'].unique())
        sorted_groups = [
            f"{group}_bw" if i % 2 == 0 else f"{group}_fw"
            for group in sorted_variations
            for i in range(2)
            ]
    else:
        sorted_groups = sorted(df['variation'].unique())


    positions = [i + 1 for i in range(len(sorted_groups))]  # Define positions for each group

    # Draw the box plot without fliers and with colors
    medianprops = dict(color='red')
    for i, (group, color) in enumerate(zip(sorted_groups, colors)):
        if SeparateScanDir:
            # Separate data into backward and forward scan directions
            if group.endswith("_bw"):
                base_group = group[:-3]  # Remove "_bw" suffix
                group_data = df[
                    (df['variation'] == base_group) & 
                    (df['scan_direction'] == 'backwards')
                ][jv_quantity].dropna()
            elif group.endswith("_fw"):
                base_group = group[:-3]  # Remove "_fw" suffix
                group_data = df[
                    (df['variation'] == base_group) & 
                    (df['scan_direction'] == 'forwards')
                ][jv_quantity].dropna()
        else:
            # Group data by variation only
            group_data = df[df['variation'] == group][jv_quantity].dropna()


        box = ax.boxplot(group_data, positions=[positions[i]], showmeans=False, showfliers=False, widths=0.5, patch_artist=True,
                          boxprops=dict(facecolor=color, color='black'),
                          medianprops=medianprops)

    # Overlay the scatter plot with black points
    for i, group in enumerate(sorted_groups):
        if SeparateScanDir:
            # Separate data into backward and forward scan directions
            if group.endswith("_bw"):
                base_group = group[:-3]  # Remove "_bw" suffix
                group_data = df[
                    (df['variation'] == base_group) & 
                    (df['scan_direction'] == 'backwards')
                ][jv_quantity].dropna()
            elif group.endswith("_fw"):
                base_group = group[:-3]  # Remove "_fw" suffix
                group_data = df[
                    (df['variation'] == base_group) & 
                    (df['scan_direction'] == 'forwards')
                ][jv_quantity].dropna()
        else:
            # Group data by variation only
            group_data = df[df['variation'] == group][jv_quantity].dropna()
        # Add jitter to x positions
        jittered_x = np.random.normal(loc=positions[i], scale=0.05, size=len(group_data))
        ax.scatter(jittered_x, group_data, color='black', alpha=1, zorder=3)

    # Axis label and Ticks
    ax.set_ylabel(f"{quantity_labels[jv_quantity]}", size=16)
    ax.set_xticks(positions)
    ax.set_xticklabels(sorted_groups, size=14, rotation=45 if len(sorted_groups) > 5 else 0,  ha='right')
    ax.set_yticks(ax.get_yticks())
    ax.tick_params(axis='both', labelsize=14)

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

    return fig
'''
    

### Function to plot EQE curves ###_____________________________________________________________________________________________________

def plot_EQE_curves(result_df,nomad_url, token):
    
    fig, ax = plt.subplots()
    
    # Define a color palette for the groups
    colors = plt.cm.viridis(np.linspace(0, 1, len(result_df)))
    
    # Set the color cycle for the axes
    ax.set_prop_cycle(color=colors)
    
    for index, row in result_df.iterrows():
        #Data from server
        eqe_data = get_specific_data_of_sample(row[f'maximum_efficiency_id'],'EQEmeasurement', nomad_url, token)
        #Relevant arrays
        wavelength_array = eqe_data[0]['eqe_data'][0]['wavelength_array']
        eqe_array = eqe_data[0]['eqe_data'][0]['eqe_array']
        #eqe_data[0]['eqe_data'][0]['integrated_jsc']
        #eqe_data[0]['eqe_data'][0]['bandgap_eqe']
        #Plot
        ax.plot(wavelength_array, eqe_array, label=f"{row['category']}", color=colors[index])
        print(row[f'maximum_efficiency_id'])
                        

    # Plot settings
    ax.legend()
    ax.set_xlim(300, 900)
    ax.set_ylim(0, 1)
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

def plot_MPP_curves(result_df, nomad_url, token):
    
    fig, ax = plt.subplots()
    
    # Define a color palette for the groups
    colors = plt.cm.viridis(np.linspace(0, 1, len(result_df)))
    
    # Set the color cycle for the axes
    ax.set_prop_cycle(color=colors)
    
    for index, row in result_df.iterrows():
        #Data from server
        mpp_data = get_specific_data_of_sample(row[f'maximum_efficiency_id'],'MPPTracking', nomad_url, token)
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