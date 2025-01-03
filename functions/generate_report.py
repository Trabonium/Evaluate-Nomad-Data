import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

from functions.plotting_functions import plot_JV_curves, plot_box_and_scatter, plot_EQE_curves, plot_MPP_curves

### Function to generate PDF report ###__________________________________________________________________________________________________

def generate_pdf_report(result_df, df, quantities, report_title):
    with PdfPages(report_title) as pdf:
        # Plot the maximum JV curves
        fig_max = plot_JV_curves(result_df, 'maximum_efficiency')
        pdf.savefig(fig_max, dpi=300, transparent=True, bbox_inches='tight')
        plt.close(fig_max)

        # Plot the median JV curves
        fig_med = plot_JV_curves(result_df, 'closest_median')
        pdf.savefig(fig_med, dpi=300, transparent=True, bbox_inches='tight')
        plt.close(fig_med)

        # Add any other plots or content to the PDF here
        fig_eff = plot_box_and_scatter(df, df['variation'], 'efficiency')
        pdf.savefig(fig_eff, dpi=300, transparent=True, bbox_inches='tight')
        plt.close(fig_eff)
        
        fig_ff = plot_box_and_scatter(df, df['variation'], 'fill_factor')
        pdf.savefig(fig_ff, dpi=300, transparent=True, bbox_inches='tight')
        plt.close(fig_ff)
        
        fig_voc = plot_box_and_scatter(df, df['variation'], 'open_circuit_voltage')
        pdf.savefig(fig_voc, dpi=300, transparent=True, bbox_inches='tight')
        plt.close(fig_voc)
        
        fig_jsc = plot_box_and_scatter(df, df['variation'], 'short_circuit_current_density')
        pdf.savefig(fig_jsc, dpi=300, transparent=True, bbox_inches='tight')
        plt.close(fig_jsc)
        
        # Add result_df as a table to the PDF
        fig_table, ax_table = plt.subplots(figsize=(10, 5))
        ax_table.axis('off')  # Hide axis
        table = ax_table.table(result_df, colLabels=result_df.columns, loc='center')
        table.auto_set_font_size(False)
        table.set_fontsize(8)
        pdf.savefig(fig_table, dpi=300, transparent=True, bbox_inches='tight')
        plt.close(fig_table)

    print("PDF report generated successfully.")