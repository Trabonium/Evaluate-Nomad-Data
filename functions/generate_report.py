import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from functions.plotting_functions import plot_JV_curves, plot_box_and_scatter, plot_EQE_curves, plot_MPP_curves, plot_hysteresis

### Updated Function to Generate PDF Report ###__________________________________________________________________________

import re
import os

# Sanitize filename (remove invalid characters)
def sanitize_filename(filename):
    return re.sub(r'[\/:*?"<>|]', '_', filename)

# Generate PDF Report
def generate_pdf_report(df, result_df, best_df, include_plots, report_title, nomad_url, token, filter_cycle_boolean):
    """
    Generates a PDF report with selected plots and data tables.

    Parameters:
        result_df (DataFrame): The statistics DataFrame.
        df (DataFrame): The original data DataFrame.
        report_title (str): The filename of the PDF report.
        include_plots (dict): Dictionary of boolean values to include specific plots. Keys:
                              - 'JV'
                              - 'Box+Scatter'
                              - 'EQE'
                              - 'MPP'
                              - 'Table'
    """
    # Split the path and file name
    directory, file_name = os.path.split(report_title)

    # Sanitize the file name
    file_name = sanitize_filename(file_name)

    # Ensure the file has a .pdf extension
    if not file_name.endswith('.pdf'):
        file_name += '.pdf'

    # Recombine the sanitized path
    report_title = os.path.join(directory, file_name)

    # Ensure the directory exists
    if directory and not os.path.exists(directory):
        os.makedirs(directory)
  

    # Round numerical values in result_df
    rounded_result_df = result_df.map(lambda x: round(x, 2) if isinstance(x, (int, float)) else x)
    rounded_best_df = best_df.map(lambda x: round(x, 2) if isinstance(x, (int, float)) else x)

    # Drop rows with NaN values
    df = df.dropna(subset=['efficiency'])  # Drop rows with NaN values in 'efficiency'
    result_df = result_df.dropna(subset=['maximum_efficiency']) # Drop rows with NaN values in 'maximum_efficiency'


    with PdfPages(report_title) as pdf:
        # Include JV Curves
        if include_plots.get('JV', False):
            fig_max = plot_JV_curves(result_df, 'maximum_efficiency', nomad_url, token)
            if include_plots.get('Picture', False):
                fig_max.savefig(directory+"/"+ file_name[:-4]+"_Best_JV.svg", format='svg', dpi = 800, bbox_inches = "tight", facecolor="white")
            pdf.savefig(fig_max, dpi=300, transparent=True, bbox_inches='tight')
            plt.close(fig_max)

            fig_med = plot_JV_curves(result_df, 'closest_median', nomad_url, token)
            if include_plots.get('Picture', False):
                fig_med.savefig(directory+"/"+ file_name[:-4]+"_Median_JV.svg", format='svg', dpi = 800, bbox_inches = "tight", facecolor="white")
            pdf.savefig(fig_med, dpi=300, transparent=True, bbox_inches='tight')
            plt.close(fig_med)

        # Include Box and Scatter Plots for PCE, FF, Voc, Jsc
        if include_plots.get('Box+Scatter', False):
            SeparateScanDir = include_plots.get('SeparateScan', False)
            fig = plot_box_and_scatter(df, filter_cycle_boolean, 'variation', SeparateScanDir)
            if include_plots.get('Picture', False):
                fig.savefig(directory+"/"+ file_name[:-4]+"_boxplot.svg", format='svg', dpi = 800, bbox_inches = "tight", facecolor="white")
            pdf.savefig(fig, dpi=300, transparent=True, bbox_inches='tight')
            plt.close(fig)

        if include_plots.get('Hysteresis', False):
            fig_hys = plot_hysteresis(df)
            if include_plots.get('Picture', False):
                fig_hys.savefig(directory+"/"+ file_name[:-4]+"_Hysteresis_JV.svg", format='svg', dpi = 800, bbox_inches = "tight", facecolor="white")
            pdf.savefig(fig_hys, dpi=300, transparent=True, bbox_inches='tight')
            plt.close(fig)

        # Include EQE Curves
        if include_plots.get('EQE', False):
            fig_eqe = plot_EQE_curves(df, result_df, nomad_url, token)
            if include_plots.get('Picture', False):
                fig_eqe.savefig(directory+"/"+ file_name[:-4]+"_EQE.svg", format='svg', dpi = 800, bbox_inches = "tight", facecolor="white")
            pdf.savefig(fig_eqe, dpi=300, transparent=True, bbox_inches='tight')
            plt.close(fig_eqe)

        # Include MPP Curves
        if include_plots.get('MPP', False):
            fig_mpp = plot_MPP_curves(df, result_df, nomad_url, token)
            if include_plots.get('Picture', False):
                fig_mpp.savefig(directory+"/"+ file_name[:-4]+"_MPP_JV.svg", format='svg', dpi = 800, bbox_inches = "tight", facecolor="white")
            pdf.savefig(fig_mpp, dpi=300, transparent=True, bbox_inches='tight')
            plt.close(fig_mpp)

        # Include Results Table
        if include_plots.get('Table', False):
            #Preparing results table
            #Insert line breaks in 'ID' fields (or any other long columns)
            for col in rounded_result_df.columns:
                if 'ID' in col:  # Assuming 'ID' columns might be too wide
                    rounded_result_df[col] = rounded_result_df[col].apply(lambda x: insert_line_breaks(str(x)) if isinstance(x, str) else x)
            # Create a figure for the table
            fig_table, ax_table = plt.subplots(figsize=(12, 6))
            ax_table.axis('off')  # Hide axis
            # Add the table to the figure
            table = ax_table.table(cellText=rounded_result_df.values, colLabels=result_df.columns, loc='center', cellLoc='center')
            # Set column widths
            max_width = 15  # Set a max column width for readability
            col_widths = []
            
            # Calculate the max length of content in each column
            for i, column in enumerate(rounded_result_df.columns):
                max_len = max(rounded_result_df[column].apply(lambda x: len(str(x)) if isinstance(x, str) else 0))  # Find max length of text in column
                col_widths.append(min(max_len, max_width))  # Set the width to max length or max width
            # Manually set column widths based on calculated values
            for i, width in enumerate(col_widths):
                table.auto_set_column_width([i])  # This will set the width for each column individually
            # Save table to PDF
            pdf.savefig(fig_table, dpi=300, transparent=True, bbox_inches='tight')
            plt.close(fig_table)
                    #Preparing best results table
            # Create a figure for the table
            fig_table2, ax_table2 = plt.subplots(figsize=(12, 6))
            ax_table2.axis('off')  # Hide axis
            # Add the table to the figure
            table2 = ax_table2.table(cellText=rounded_best_df.values, colLabels=best_df.columns, loc='center', cellLoc='center')
             
            # Set column widths
            max_width = 15  # Set a max column width for readability
            col_widths = []
            # Calculate the max length of content in each column
            for i, column in enumerate(rounded_best_df.columns):
                max_len = max(rounded_best_df[column].apply(lambda x: len(str(x)) if isinstance(x, str) else 0))  # Find max length of text in column
                col_widths.append(min(max_len, max_width))  # Set the width to max length or max width
                    # Manually set column widths based on calculated values
            for i, width in enumerate(col_widths):
                table2.auto_set_column_width([i])  # This will set the width for each column individually
            # Save table to PDF
            pdf.savefig(fig_table2, dpi=300, transparent=True, bbox_inches='tight')
            plt.close(fig_table2)

    print("PDF report generated successfully.")
    return(directory, file_name)

def insert_line_breaks(text):
    """
    Insert line breaks after every 15 characters at the first '_'.
    """
    # Split the string into chunks of 15 characters
    chunked_text = [text[i:i+15] for i in range(0, len(text), 15)]
    
    # Join the chunks with line breaks
    return '\n'.join(chunked_text).replace('_', '\n', 1)  # Replace the first '_' with a line break
