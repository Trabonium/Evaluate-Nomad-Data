import numpy as np
import pandas as pd
from scipy.stats import f_oneway
from statsmodels.stats.multicomp import pairwise_tukeyhsd

### Function to calculate statistics of data ###_____________________________________________________________________________________

def calculate_statistics(df):    

    result_df = pd.DataFrame(columns=['category',
                                      'standard_deviation',
                                      'median',
                                      'closest_median',
                                      'closest_median_id',
                                      'maximum_efficiency',
                                      'maximum_efficiency_id'])

    for index, category in enumerate(sorted(df['variation'].unique())):
        # Calculate standard deviation
        std_dev = df[df['variation'] == category]['efficiency'].std()
        # Median and closest value to median
        med_eff = df[df['variation'] == category]['efficiency'].median()
        closest_med_eff_value = sorted(df[df['variation'] == category]['efficiency'],
                                       key=lambda x: abs(x - med_eff - 0.000000001))[:1]
        med_id = df[df['efficiency'] == closest_med_eff_value[0]]['sample_id'].values[0]
        # Maximum efficiency value
        max_eff = df[df['variation'] == category]['efficiency'].max()
        max_id = df[df['efficiency'] == max_eff]['sample_id'].values[0]

        # Create a temporary DataFrame with the current results
        temp_df = pd.DataFrame({
            'category': [category],
            'standard_deviation': [np.round(std_dev,2)],
            'median': [np.round(med_eff)],
            'closest_median': [closest_med_eff_value[0]],
            'closest_median_id': [med_id],
            'maximum_efficiency': [max_eff],
            'maximum_efficiency_id': [max_id]
            })

        # Concatenate the temporary DataFrame with the result DataFrame
        result_df = pd.concat([result_df, temp_df], ignore_index=True)

    # Perform ANOVA test
    f_statistic, p_value = f_oneway(*[group['efficiency'] for name, group in df.groupby(quantities[0])])

    if p_value < 0.05:
        # Perform Tukey HSD test
        tukey_results = pairwise_tukeyhsd(df['efficiency'], df['variation'], alpha=0.05)
        print(tukey_results)
    else:
        print("No significant differences between group means.")
            
    return result_df
