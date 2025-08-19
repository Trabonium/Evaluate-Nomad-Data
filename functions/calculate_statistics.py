import numpy as np
import pandas as pd
from scipy.stats import f_oneway
from statsmodels.stats.multicomp import pairwise_tukeyhsd

def calculate_statistics(df: pd.DataFrame):    
    """
    Calculates statistical measures for efficiency values grouped by the 'variation' column.

    Input:
    -----------
    df : pd.DataFrame
        DataFrame containing at least the following columns:
        - 'variation' (str): Category grouping the samples.
        - 'efficiency' (float): Efficiency values to analyze.
        - 'sample_id' (str or int): Identifier for each sample.
        - 'px#' (str or int): Measurement identifier.
        - 'open_circuit_voltage' (float): Open circuit voltage values.
        - 'fill_factor' (float): Fill factor values.
        - 'short_circuit_current_density' (float): Short-circuit current density.

    Returns:
    --------
    tuple[pd.DataFrame, pd.DataFrame]
        - result_df: DataFrame with statistical measures per category.
        - best_df: DataFrame with the best-performing sample per category.
    """

    result_df = pd.DataFrame(columns=[
        'category',
        'standard_deviation',
        'median',
        'closest_median',
        'closest_median_id',
        'maximum_efficiency',
        'maximum_efficiency_id'
    ])
    
    best_df = pd.DataFrame(columns=[
        'category',
        'sample_id',
        'px',
        'PCE',
        'Voc',
        'FF',
        'Jsc'
    ])
    print('output: \n',pd.unique(df['variation'])[::-1])
    for category in pd.unique(df['variation'])[::-1]:
        category_data = df[df['variation'] == category]

        if category_data.empty or category_data['efficiency'].dropna().empty:
            # If no data, add a row with None values and skip further calculations
            temp_df = pd.DataFrame({
                'category': [category],
                'standard_deviation': [None],
                'median': [None],
                'closest_median': [None],
                'closest_median_id': [None],
                'median_px': [None],
                'maximum_efficiency': [None],
                'maximum_efficiency_id': [None],
                'max_px': [None]
            })
            
            best_df_temp = pd.DataFrame({
                'category': [category],
                'sample_id': [None],
                'px': [None],
                'PCE': [None],
                'Voc': [None],
                'FF': [None],
                'Jsc': [None]
            })

        else:
            # Normal statistics calculations
            std_dev = category_data['efficiency'].std()
            med_eff = category_data['efficiency'].median()
            closest_med_eff_value = sorted(category_data['efficiency'].dropna(),
                                           key=lambda x: abs(x - med_eff - 0.000000001))[:1]
            med_id = category_data[category_data['efficiency'] == closest_med_eff_value[0]]['sample_id'].values[0]
            max_eff = category_data['efficiency'].max()
            max_id = category_data[category_data['efficiency'] == max_eff]['sample_id'].values[0]

            temp_df = pd.DataFrame({
                'category': [category],
                'standard_deviation': [np.round(std_dev,2)],
                'median': [np.round(med_eff,2)],
                'closest_median': [closest_med_eff_value[0]],
                'closest_median_id': [med_id],
                'median_px': [category_data[category_data['efficiency'] == closest_med_eff_value[0]]['px#'].values[0]],
                'maximum_efficiency': [max_eff],
                'maximum_efficiency_id': [max_id],
                'max_px': [category_data[category_data['efficiency'] == max_eff]['px#'].values[0]]
            })

            best_df_temp = pd.DataFrame({
                'category': [category],
                'sample_id': [max_id],
                'px': [category_data[category_data['efficiency'] == max_eff]['px#'].values[0]],
                'PCE': [max_eff],
                'Voc' : [category_data[category_data['efficiency'] == max_eff]['open_circuit_voltage'].values[0]],
                'FF' : [category_data[category_data['efficiency'] == max_eff]['fill_factor'].values[0]],
                'Jsc' : [category_data[category_data['efficiency'] == max_eff]['short_circuit_current_density'].values[0]]
            })

        # Concatenate the results
        result_df = pd.concat([result_df, temp_df], ignore_index=True)
        best_df = pd.concat([best_df, best_df_temp], ignore_index=True)

    # Perform ANOVA test
    if len(df['variation'].unique()) > 1 and not df['efficiency'].dropna().empty:
        f_statistic, p_value = f_oneway(*[group['efficiency'].dropna().values for _, group in df.groupby('variation')])
        
        if p_value < 0.05:
            # Perform Tukey HSD test
            tukey_results = pairwise_tukeyhsd(df['efficiency'], df['variation'], alpha=0.05)
            print(tukey_results)
        else:
            print("No significant differences between group means.")

    return result_df, best_df
