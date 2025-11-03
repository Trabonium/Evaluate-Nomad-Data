import matplotlib as mpl
mpl.use("Agg")
'''
makes it impossible to use matplotlib GUI here (eg show()) but otherwise we get problems with the side thread
'''
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
import numpy as np
import pandas as pd
import math
from scipy.stats import linregress
from functions.api_calls_get_data import get_specific_data_of_sample

def get_smart_axis_limits(data, quantity_name):
    """
    Get smart axis limits based on the quantity type and data range.
    
    Args:
        data: array-like, data values
        quantity_name: str, name of the quantity being plotted
    
    Returns:
        tuple: (y_min, y_max) with smart limits
    """
    if len(data) == 0:
        return 0, 1
    
    data_clean = data.dropna() if hasattr(data, 'dropna') else np.array(data)[~np.isnan(data)]
    if len(data_clean) == 0:
        return 0, 1
        
    data_min, data_max = np.min(data_clean), np.max(data_clean)
    data_range = data_max - data_min
    
    if quantity_name == 'efficiency':
        # PCE: round to nearest 5% for wide ranges, 1% for narrow ranges
        if data_range > 10:
            return 0, math.ceil(data_max / 5) * 5
        elif data_range > 5:
            return math.floor(data_min), math.ceil(data_max)
        else:
            # For narrow ranges, add some padding
            padding = max(1, data_range * 0.1)
            return max(0, math.floor(data_min - padding)), math.ceil(data_max + padding)
    
    elif quantity_name == 'fill_factor':
        # FF: use 0.1 increments, typically between 0.3-0.9
        y_min = math.floor(data_min * 10) / 10
        y_max = math.ceil(data_max * 10) / 10
        # Ensure reasonable bounds for fill factor
        y_min = max(0.0, y_min - 0.05)
        y_max = min(1.0, y_max + 0.05)
        return y_min, y_max
    
    elif quantity_name == 'open_circuit_voltage':
        # Voc: use 0.1V increments, typically between 0.8-1.3V
        y_min = math.floor(data_min * 10) / 10
        y_max = math.ceil(data_max * 10) / 10
        # Add small padding
        y_min = max(0.0, y_min - 0.05)
        y_max = y_max + 0.05
        return y_min, y_max
    
    elif quantity_name == 'short_circuit_current_density':
        # Jsc: round to nearest integer, typically 10-25 mA/cm²
        if data_range > 10:
            return math.floor(data_min / 5) * 5, math.ceil(data_max / 5) * 5
        else:
            return math.floor(data_min), math.ceil(data_max)
    
    else:
        # Default case: add 10% padding and round nicely
        padding = max(0.1, data_range * 0.1)
        y_min = data_min - padding
        y_max = data_max + padding
        
        # Try to round to nice numbers
        if data_range > 10:
            return math.floor(y_min), math.ceil(y_max)
        elif data_range > 1:
            return math.floor(y_min * 10) / 10, math.ceil(y_max * 10) / 10
        else:
            return math.floor(y_min * 100) / 100, math.ceil(y_max * 100) / 100

# Custom color palette for specific groups (Daniel's colors)
DANIEL_COLORS = {
    'RepA': '#001898',
    'RepB': '#006D94', 
    'ref1': '#00876C',
    'ref2': '#00876C',
    'RepC': '#33AD59',
    'RepE': '#66CB66',
    'RepD': '#AFE399',  # excluded group
    
    # ROB series colors
    'ref1': '#00876C',    # Rob Ref (same as Rob Ref)
    'h=30': '#A03E63',    # h30
    'h=25': '#DD85AB',    # h25
    'tQ=38,5': '#500D63',    # tQ
    'tQ=31,5': '#95409A',    # tQ (variant)
    'td=17': '#23003C',    # td
    'Q=55': '#10E0C9',    # Q
    'Q=45': '#3EFEDD',    # Q (variant)
    'ref2': '#00876C',    # Rob Ref (same as Rob Ref)
    'P=2,7': '#FFC548',   # P
    'P=3,3': '#FF9965',   # P (variant)
    'A=5,4': '#7E5F5E',   # A (variant)
    'A=4,5': '#947A72'    # A (variant)
}

### Function to plot JV curves ###______________________________________________________________________________________________________

def plot_JV_curves(result_df, curve_type, nomad_url, token):

    fig, ax = plt.subplots()
    
    # Create category-to-color mapping using Daniel's custom colors
    unique_categories = result_df['category'].unique()
    category_colors = {}
    
    # Use custom colors for known categories, fallback to viridis for unknown ones
    viridis_fallback = plt.cm.viridis(np.linspace(0, 0.95, len(unique_categories)))
    fallback_idx = 0
    
    for category in unique_categories:
        if category in DANIEL_COLORS:
            category_colors[category] = DANIEL_COLORS[category]
        else:
            category_colors[category] = viridis_fallback[fallback_idx]
            fallback_idx += 1
    
    max_Voc = 0
    PCE = None
    for index, row in result_df.iterrows():
        jv_data = get_specific_data_of_sample(row[f'{curve_type}_id'], "JVmeasurement", nomad_url, token)
        found_curve = False  # Flag to stop both loops
        for cell in jv_data:
            for i in range(2):
                try:
                    PCE = cell["jv_curve"][i]["efficiency"]
                    if PCE == row[f'{curve_type}'] and \
                   (curve_type == 'maximum_efficiency' or curve_type == 'closest_median'):
                        # Get the color for this category
                        category_color = category_colors[row['category']]
                        
                        if mpl.rcParams["text.usetex"]:
                            ax.plot(cell["jv_curve"][i]["voltage"], \
                                    cell["jv_curve"][i]["current_density"], \
                                    color=category_color, \
                                    label=fr"{row['category']}: {round(PCE,2)}\%")
                        else:
                            ax.plot(cell["jv_curve"][i]["voltage"], \
                                    cell["jv_curve"][i]["current_density"], \
                                    color=category_color, \
                                    label=f"{row['category']}: {round(PCE,2)}%")
                        if max_Voc < max(cell["jv_curve"][i]["voltage"]):
                            max_Voc = max(cell["jv_curve"][i]["voltage"])
                        found_curve = True
                        break
                except:
                    continue
                
            if found_curve: #Stops plotting duplicates in the same configuration
                break 

    # Plot settings
    ax.legend()
    if max_Voc < 1.3:
        ax.set_xlim(-0.2, 1.3)
    else:   
        ax.set_xlim(-0.2, ((math.ceil(max_Voc * 10))/10) + 0.1) 
    ax.set_ylim(-5, 25)
    ax.set_xlabel('Voltage (V)')
    if curve_type == 'maximum_efficiency':
        ax.set_ylabel('(Best) Current Density (mA/cm²)')
    else:
        ax.set_ylabel('(Median) Current Density (mA/cm²)')

    # Axis ticks and borders
    ax.tick_params(axis='both', which='both', direction='in', width=2, bottom=1, top=1, left=1, right=1)
 
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
        
        #correction -> EQE is max 1.00 instead of 100% + same wavelength for all EQE curves
        wavelength_array = eqe_data[0]['eqe_data'][0]['wavelength_array']
        eqe_array = [w * 100 for w in eqe_data[0]['eqe_data'][0]['eqe_array']]
        if max_EQE < max(eqe_array):
            max_EQE = max(eqe_array)
        if wellenlenge_min > min(wavelength_array):
            wellenlenge_min = min(wavelength_array)
        if wellenlenge_max < max(wavelength_array):
            wellenlenge_max = max(wavelength_array)
        ax.plot(wavelength_array, eqe_array, color=colors[index], label=f"{row['category']}: {round(eqe_data[0]['eqe_data'][0]['integrated_jsc'],2)} mA/cm² {round(eqe_data[0]['eqe_data'][0]['bandgap_eqe'],2)} eV")
        #print(row[f'maximum_efficiency_id'])
                        
    # Plot settings
    yticks = [i for i in range(0,math.ceil(max_EQE/10)*10+10,10)] #erstellt eine liste von 0 bis max EQE bis auf 10 aufgerundet in 10er schritten
    ax.set_yticks(yticks)
    ax.set_ylim(0, max(yticks))
    ax.legend()
    ax.set_xlim(wellenlenge_min-20, wellenlenge_max+20)
    ax.set_title(f'EQE Curves')
    ax.set_xlabel('Wavelength (nm)')
    if mpl.rcParams["text.usetex"]:
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

        # Schritt 1: Maximum finden
        max_idx = np.argmax(pce_array)
        P_max = pce_array[max_idx]
        P_80 = 0.8 * P_max

        # Schritt 2: Fit ab Maximum
        x_fit = time_array[max_idx:]
        y_fit = pce_array[max_idx:]
        slope, intercept, *_ = linregress(x_fit, y_fit)

        # Schritt 3: Schnittpunkt mit P_80 berechnen
        # P_80 = slope * x_T80 + intercept  →  x_T80 = (P_80 - intercept) / slope
        x_T80 = (P_80 - intercept) / slope
        #Plot
        ax.plot(time_array, pce_array, label=f"{row['category']} | T80 = {x_T80:.1f}s", color=colors[index])
        ax.hlines(y=max(pce_array), xmin=0, xmax=300, colors=colors[index], linestyles='--', linewidth=.5)
        print(row[f'maximum_efficiency_id'])
                        
 
    # Plot settings
    ax.legend()
    ax.set_xlim(0, 300)
    #ax.set_ylim(0, 25)
    ax.set_title(f'MPP Tracking')
    ax.set_xlabel('Time (s)')
    if mpl.rcParams["text.usetex"]:
        ax.set_ylabel(r'PCE (\%)')
    else:
        ax.set_ylabel('PCE (%)')

    # Axis ticks and borders
    ax.tick_params(axis='both', which='both', direction='in', width=2, bottom=1, top=1, left=1, right=1)

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

def plot_box_and_scatter(df, filter_cycle_boolean, quantity=['variation'], SeparateScanDir=False):
    
    
    # Create category-to-color mapping using Daniel's custom colors
    unique_categories = df[quantity].unique()
    category_colors = {}
    
    # Use custom colors for known categories, fallback to viridis for unknown ones
    viridis_fallback = plt.cm.viridis(np.linspace(0, 0.95, len(unique_categories)))
    fallback_idx = 0
    
    for category in unique_categories:
        if category in DANIEL_COLORS:
            category_colors[category] = DANIEL_COLORS[category]
        else:
            category_colors[category] = viridis_fallback[fallback_idx]
            fallback_idx += 1
    
    # Convert to list for compatibility with existing code
    base_colors = [category_colors[cat] for cat in unique_categories]

    if SeparateScanDir:
        # Extend the colors for 'forward' groups by shifting brightness
        bw_colors = base_colors
        
        # Convert hex colors to RGBA with transparency for forward scans
        fw_colors = []
        for color in base_colors:
            if isinstance(color, str):  # hex color
                # Convert hex to RGB, then add transparency
                import matplotlib.colors as mcolors
                rgb = mcolors.to_rgb(color)
                fw_colors.append((rgb[0], rgb[1], rgb[2], 0.5))
            else:  # already RGBA tuple
                fw_colors.append((color[0], color[1], color[2], 0.5))

        # Combine backwards and forwards colors interleaved
        colors = []
        for bw_color, fw_color in zip(bw_colors, fw_colors):
            colors.append(bw_color)  # Backward color
            colors.append(fw_color)  # Forward color
    else:
        # Use only the base color palette
        colors = base_colors

    # take original order
    sorted_variations = pd.unique(df[quantity])
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
    if mpl.rcParams["text.usetex"]:
        jv_quantity_labels = {
        'open_circuit_voltage': r"$\mathrm{V_{oc} \, (V)}$",
        'fill_factor': "FF",
        'efficiency': r"PCE (\%)",
        'short_circuit_current_density': r"$\mathrm{J_{sc} \, (mA/cm²)}$"
    }
    else:
        jv_quantity_labels = {
            'open_circuit_voltage': r"$\mathrm{V_{oc} \, (V)}$",
            'fill_factor': "FF",
            'efficiency': "PCE (%)",
            'short_circuit_current_density': r"$\mathrm{J_{sc} \, (mA/cm²)}$"
        }

    #Define markers for different cycles
    scatter_cycle_marker = {
        1: 'o',
        2: 's',
        3: '^',
        4: 'd',
        5: 'p',
        6: 'h',
        7: 'v',
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
                        (df[quantity].astype(str) == str(base_group)) & 
                        (df['scan_direction'] == 'backwards')
                    ][jv_quantity[i]].dropna()
                    # Apply shift to the left for backward scans
                    group_position = positions[j]/2 + 0.3
                elif group.endswith("_fw"):
                    base_group = group[:-3]  # Remove "_fw" suffix
                    group_data = df[
                        (df[quantity].astype(str) == str(base_group)) & 
                        (df['scan_direction'] == 'forwards')
                    ][jv_quantity[i]].dropna()
                    # Apply shift to the right for forward scans
                    group_position = positions[j]/2 + 0.2
            else:
                # Group data by variation only
                group_data = df[df[quantity].astype(str) == str(group)][jv_quantity[i]].dropna()
                group_position = positions[j]

            # Plot the boxplot
            ax.boxplot(group_data, positions=[group_position], showmeans=False, showfliers=False, widths=0.4, patch_artist=True,
                       boxprops=dict(facecolor=color, color='black'),
                       medianprops=medianprops)
            
        if filter_cycle_boolean: #hier optimum
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
                        group_data = df[(df[quantity] == group)][jv_quantity[i]].dropna()
                        group_position = positions[j]

                    # Add jitter to x positions
                    jittered_x = np.random.normal(loc=group_position, scale=0.05, size=len(group_data))
                    ax.scatter(jittered_x, group_data, color='black', alpha=0.9, zorder=2, s=25, marker='o')

        else: #falls nur nans sind geht das hier schief das muss extra abgedeckt werden
            if df['Cycle#'].isna().all():
                alpha = 0.9 
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
                        group_data = df[(df[quantity] == group)][jv_quantity[i]].dropna()
                        group_position = positions[j]

                    # Add jitter to x positions
                    jittered_x = np.random.normal(loc=group_position, scale=0.05, size=len(group_data))
                    ax.scatter(jittered_x, group_data, color='black', alpha=alpha, zorder=2, s=25, marker=scatter_cycle_marker[1])

                
            else:
                for k, cyclegroup in enumerate(sorted(df['Cycle#'].dropna().unique())):
                    alpha = 0.9 - k / len(df['Cycle#'].unique())
                    # Overlay the scatter plot with black points
                    for j, group in enumerate(sorted_groups):
                        if SeparateScanDir:
                            # Separate data into backward and forward scan directions
                            if group.endswith("_bw"):
                                base_group = group[:-3]  # Remove "_bw" suffix
                                group_data = df[
                                    (df[quantity] == base_group) & 
                                    (df['scan_direction'] == 'backwards') &
                                    (df['Cycle#'] == cyclegroup)
                                ][jv_quantity[i]].dropna()
                                # Apply shift to the left for backward scans
                                group_position = positions[j]/2 + 0.3
                            elif group.endswith("_fw"):
                                base_group = group[:-3]  # Remove "_fw" suffix
                                group_data = df[
                                    (df[quantity] == base_group) & 
                                    (df['scan_direction'] == 'forwards') &
                                    (df['Cycle#'] == cyclegroup)
                                ][jv_quantity[i]].dropna()
                                # Apply shift to the right for forward scans
                                group_position = positions[j]/2 + 0.2
                        else:
                            # Group data by variation only
                            group_data = df[(df[quantity] == group) & (df['Cycle#'] == cyclegroup)][jv_quantity[i]].dropna()
                            group_position = positions[j]

                        # Add jitter to x positions
                        jittered_x = np.random.normal(loc=group_position, scale=0.05, size=len(group_data))
                        ax.scatter(jittered_x, group_data, color='black', alpha=alpha, zorder=2, s=25, marker=scatter_cycle_marker[k+1])
        

        
        
        # Axis label and Ticks
        ax.set_ylabel(f"{jv_quantity_labels[jv_quantity[i]]}", size=16)
        ax.set_xticks([i + 1 for i in range(len(sorted_variations))])
        ax.set_xticklabels(sorted_variations, size=14, rotation=45 if len(sorted_variations) > 4 else 0, ha='right' if len(sorted_variations) > 4 else 'center')
        # Apply smart y-axis limits
        y_min, y_max = get_smart_axis_limits(df[jv_quantity[i]].dropna(), jv_quantity[i])
        ax.set_ylim(y_min, y_max)
        ax.yaxis.set_major_locator(MaxNLocator(nbins=6, steps=[1, 2, 5, 10])) 
        ax.tick_params(axis='both')
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

    # Use consistent subplot spacing instead of tight_layout to ensure uniform plot dimensions
    # This prevents variable x-label lengths from affecting plot box sizes
    plt.subplots_adjust(
        left=0.08,      # Left margin
        right=0.95,     # Right margin  
        top=0.95,       # Top margin
        bottom=0.2,    # Bottom margin (extra space for rotated labels)
        wspace=0.15,    # Width spacing between subplots
        hspace=0.25     # Height spacing between subplots
    )
    
    return fig

#hysteresis plot function
def plot_hysteresis(df): #quantity is here default 'variation'

    # Berechnung der Quotienten für jede Variation
    quotient_data = []
    for i, variation in enumerate(df['variation'].unique()):
        subset = df[df['variation'] == variation]
        backwards = subset[subset['scan_direction'] == 'backwards']['efficiency'].values
        forwards = subset[subset['scan_direction'] == 'forwards']['efficiency'].values
        
        quotient = (backwards - forwards) / backwards  # Elementweise Division
        for q in quotient:
            quotient_data.append({'variation': variation, 'quotient': q})

    df_quotient = pd.DataFrame(quotient_data)

    # Farben für die Boxplots
    base_colors = plt.cm.viridis(np.linspace(0, 0.95, len(df_quotient['variation'].unique())))
    colors = base_colors

    #original order
    sorted_variations = pd.unique(df_quotient['variation'])

    # Boxplot-Setup
    fig, ax = plt.subplots(figsize=(8, 6))

    positions = [i + 1 for i in range(len(sorted_variations))]  # X-Positionen

    # Boxplots erstellen
    medianprops = dict(color='red')

    for j, (group, color) in enumerate(zip(sorted_variations, colors)):
        group_data = df_quotient[df_quotient['variation'] == group]['quotient'].dropna()
        group_position = positions[j]

        # Boxplot zeichnen
        ax.boxplot(group_data, positions=[group_position], showmeans=False, showfliers=False, widths=0.4, patch_artist=True,
                boxprops=dict(facecolor=color, color='black'),
                medianprops=medianprops)

    # Scatterplot überlagern
    for j, group in enumerate(sorted_variations):
        group_data = df_quotient[df_quotient['variation'] == group]['quotient'].dropna()
        group_position = positions[j]

        # Jitter für Streuung hinzufügen
        jittered_x = np.random.normal(loc=group_position, scale=0.05, size=len(group_data))
        ax.scatter(jittered_x, group_data, color='black', alpha=0.9, zorder=2, s=25)

    # Achsenbeschriftung
    ax.set_ylabel("Hysteresis", size=16)
    ax.set_xticks(positions)
    ax.set_xticklabels(sorted_variations, size=14)
    ax.yaxis.set_major_locator(MaxNLocator(nbins=6, steps=[1, 2, 5, 10])) 
    ax.tick_params(axis='both')
    ax.grid(axis='y', color='grey', linestyle='--', linewidth=0.5, alpha=0.5) 

    # Rahmen & Achsenticks formatieren
    ax.spines['bottom'].set_linewidth(2)
    ax.spines['left'].set_linewidth(2)
    ax.spines['top'].set_linewidth(2)
    ax.spines['right'].set_linewidth(2)
    ax.tick_params(axis='both', right=True, top=True, direction='in', width=2, colors='black', length=5)

    # Layout anpassen und Plot anzeigen
    plt.tight_layout()
    
    return fig
