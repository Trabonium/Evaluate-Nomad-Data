#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from matplotlib.backends.backend_pdf import PdfPages
from openpyxl import load_workbook
import pandas as pd

from functions.api_calls_get_data import get_entryid, get_quantity_over_jv


### Function to get data from excel and server  ###_____________________________________________________________________________________

def get_data_excel_to_df(excel_file_path, nomad_url, token):
    
    #file_path = path + "ExperimentsInfo.xlsx"  
    
    workbook = load_workbook(filename=excel_file_path, data_only=True)
    sheet = workbook.active  # Access the active worksheet

    # Extract data from columns 6 (sample_id) and 7 (group names)
    data = []
    for row in sheet.iter_rows(min_row=3, min_col=6, max_col=7, values_only=True):
        sample_id, group_name = row
        data.append((sample_id, group_name))

    # Convert the extracted data to a DataFrame
    excel_df = pd.DataFrame(data, columns=["sample_id", "variation"])

    df, quantities = get_batch_data(excel_df["sample_id"].unique(), nomad_url, token)
    # Merge with the existing DataFrame on 'sample_id'
    # Assume `df` is your existing DataFrame
    df = excel_df.merge(df, on="sample_id", how="left")

    # Print the updated DataFrame
    #print(df)
    return df


### Function to get data from the server and process it ###_________________________________________________________________________

def get_batch_data(sample_ids, nomad_url, token):
    #Get the NOMAD ID
    samples_of_batch = [(sample_id, get_entryid(sample_id, nomad_url, token)) for sample_id in sample_ids]

    #Process in which the quantity was changed
    #TODO Make this a variable input as dropdown menu
    key = ["peroTF_CR_SpinBox_SpinCoating"]
    
    #Varied quantities to extract 
    #TODO Make this a variable input as dropdown menu - or from excel file
    quantities=["name"]
    
    #Standard JV parameters to get
    jv_quantities=["efficiency",\
                   "fill_factor",\
                   "open_circuit_voltage",\
                   "short_circuit_current_density"]
    
    #Get data
    df = get_quantity_over_jv(samples_of_batch, key, quantities, jv_quantities, nomad_url, token)
    
    #Extract Information from ID
    df['last_digit'] = df['sample_id'].str.extract('(\d)$').astype(int)[0]
    df['category'] = df['sample_id'].str.split('_').str[4]
    df['batch_name'] = df['sample_id'].str.split('_').str[3]
    df['batch_date'] = df['sample_id'].str.split('_').str[2]

    # Data cleaning remove shunted or somehow damaged devices using filters
    df = df[df['fill_factor'] >= 0.5]
    df = df[df['open_circuit_voltage'] >= 1]
    df = df[df['short_circuit_current_density'] <= 30]
    df = df[df["fill_factor"] <= 1]


    return df, quantities






