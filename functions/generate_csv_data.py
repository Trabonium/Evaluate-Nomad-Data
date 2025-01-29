import pandas as pd

def generate_csv_raw_file(file_path, raw_data):
    raw_data_real_withoutNaN = raw_data['efficiency'].notna().sum()
    raw_data_real_withNaN = len(raw_data['efficiency'])
    raw_NaN_data_yield = f"{100* raw_data_real_withoutNaN/ (raw_data_real_withNaN)} %"
    r_zusatzdaten = {"Data Yield (all data - NaN) / all data": [raw_NaN_data_yield]}
    raw_zusatzdaten = pd.DataFrame(r_zusatzdaten)
    df_raw_copy = pd.concat([raw_data, raw_zusatzdaten], ignore_index=True)
    df_raw_copy.to_csv(file_path, sep=";", index=False)
    return


def generate_csv_filtered_file(file_path, raw_data, filtered_data, df_min_max_filter):
    absolute_data_yield = f"{100 * len(filtered_data['efficiency']) / len(raw_data['efficiency'])} %"
    f_zusatzdaten = {"(all data - NaNs - filtered data) / all data": [absolute_data_yield]}
    filtered_zusatzdaten = pd.DataFrame(f_zusatzdaten)
    df_filtered_copy = pd.concat([filtered_data, filtered_zusatzdaten, df_min_max_filter], ignore_index=True)
    df_filtered_copy.to_csv(file_path, sep=";", index=False)
    return