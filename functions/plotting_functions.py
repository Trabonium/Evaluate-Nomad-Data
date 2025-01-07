import matplotlib.pyplot as plt
import numpy as np

from functions.api_calls_get_data import get_specific_data_of_sample


### Function to plot JV curves ###______________________________________________________________________________________________________

def plot_JV_curves(result_df, curve_type, nomad_url, token):
    fig, ax = plt.subplots()
    
    # Define a color palette for the groups
    colors = plt.cm.viridis(np.linspace(0, 1, len(result_df)))
    
    # Set the color cycle for the axes
    ax.set_prop_cycle(color=colors)
    
    for index, row in result_df.iterrows():
        jv_data = get_specific_data_of_sample(row[f'{curve_type}_id'], "JVmeasurement", nomad_url, token)
        for cell in jv_data:
            for i in range(2):
                if cell["jv_curve"][i]["efficiency"] == row[f'{curve_type}'] and \
                   (curve_type == 'maximum_efficiency' or curve_type == 'closest_median'):
                        ax.plot(cell["jv_curve"][i]["voltage"], \
                                 cell["jv_curve"][i]["current_density"], \
                                 label=f"{row['category']}")
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

def plot_box_and_scatter(df, quantities, jv_quantity):
    # Define a color palette for the groups
    colors = plt.cm.viridis(np.linspace(0, 1, len(df['variation'].unique())))
    
    # Define Y-Axis Labels
    quantity_labels = {
        'open_circuit_voltage': 'Open Circuit Voltage (V)',
        'fill_factor': 'Fill Factor (%)',
        'efficiency': 'Efficiency (%)',
        'short_circuit_current_density': 'Short Circuit Current Density (mA/cm²)'
    }

    fig, ax = plt.subplots(figsize=(10, 5))

    # Sort the unique variation groups first to ensure consistent order
    sorted_groups = sorted(df['variation'].unique())
    positions = [i + 1 for i in range(len(sorted_groups))]  # Define positions for each group

    # Draw the box plot without fliers and with colors
    medianprops = dict(color='red')
    for i, (group, color) in enumerate(zip(sorted_groups, colors)):
        group_data = df[df['variation'] == group][jv_quantity].dropna()
        box = ax.boxplot(group_data, positions=[positions[i]], showmeans=False, showfliers=False, widths=0.5, patch_artist=True,
                          boxprops=dict(facecolor=color, color='black'),
                          medianprops=medianprops)

    # Overlay the scatter plot with black points
    for i, group in enumerate(sorted_groups):
        group_data = df[df['variation'] == group]
        # Add jitter to x positions
        jittered_x = np.random.normal(loc=positions[i], scale=0.05, size=len(group_data))
        ax.scatter(jittered_x, group_data[jv_quantity], color='black', alpha=1, zorder=3)

    # Axis label and Ticks
    ax.set_ylabel(f"{quantity_labels[jv_quantity]}", size=16)
    ax.set_xticks(positions)
    ax.set_xticklabels(sorted_groups, size=14)
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