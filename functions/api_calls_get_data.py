#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""

"""

import requests
import pandas as pd
import numpy as np


def get_entryid(sample_ids: list[str], nomad_url: str, token):  # give it a batch id
    # get all entries related to this batch id
    query = {
        'required': {
            #'metadata': '*'
            'include': ['entry_id', 'entry_name']
        },
        'owner': 'visible',
        'query': {'results.eln.lab_ids': {'any': sample_ids}},
        'pagination': {
            'page_size': 100
        }
    }
    response = requests.post(
        f'{nomad_url}/entries/query', headers={'Authorization': f'Bearer {token}'}, json=query).json()
    data = response["data"]
    queried_ids = pd.DataFrame(data=data)

    #get remaining pages
    while (response['pagination'].get('next_page_after_value')):
        next_page = response['pagination'].get('next_page_after_value')
        query['pagination']['page_after_value'] = next_page
        response = requests.post(
        f'{nomad_url}/entries/query', headers={'Authorization': f'Bearer {token}'}, json=query).json()
        data = response['data']
        queried_ids = pd.concat([queried_ids, pd.DataFrame(data)], ignore_index=True)
    
    return queried_ids


def return_value(data, path):
    if path:
        try:
            return return_value(data[int(path[0])], path[1:])
        except:
            return return_value(data[path[0]],  path[1:])
    return data


def get_quantity_over_jv(samples_of_batch: pd.DataFrame, key_1, quantities: list[str], jv_quantities: list[str], nomad_url: str, token) -> pd.DataFrame:
    """ samples_of_batch: Dataframe with at least a column 'entry_id' with nomad entry ids
        jv_quantities: features to extract for each sample
    """
    if not isinstance(key_1, list):
        key_1 = [key_1]
    # collect the results of the sample, in this case it are all the annealing temperatures
    df_q = pd.DataFrame(columns=["entry_id","sample_id"]+quantities)
    df_jv = pd.DataFrame(columns=["entry_id"]+["px#"]+["scan_direction"]+jv_quantities)

    for index, row in samples_of_batch.iterrows():
        sample_id = row['entry_id']
        row = {"entry_id": sample_id, "sample_id":row['entry_name']}
        query = {
            'required': {
                'metadata': '*',
                'data': '*',
            },
            'owner': 'visible',
            'query': {'entry_references.target_entry_id': sample_id},
            'pagination': {
                'page_size': 100
            }
        }
        response = requests.post(f'{nomad_url}/entries/archive/query',
                                 headers={'Authorization': f'Bearer {token}'}, json=query)
        #print(response.json())
        linked_data = response.json()["data"]

        # Change code here!!!!
        for link in linked_data:
            if any([kk == link["archive"]["metadata"]["entry_type"] for kk in key_1]):
                data = link["archive"]["data"]
                for q in quantities:
                    q_split = q.split("/")

                    row.update({q: return_value(data.copy(), q_split.copy())})

        df_q.loc[len(df_q.index)] = row
        for link in linked_data:
            if "JVmeasurement" in link["archive"]["metadata"]["entry_type"]:
                row = {"entry_id": sample_id}
                for curve in link["archive"]["data"]["jv_curve"]:
                    row['px#'] = link["archive"]["data"]["description"].split(': ')[1] # extract pixel nr from notes 
                    row["scan_direction"] = (  #scan direction
                        "backwards" if curve["cell_name"] == "Current density [1] [mA/cm^2]" else
                        "forwards" if curve["cell_name"] == "Current density [2] [mA/cm^2]" else
                        None)  #scan direction
                    for quantity in jv_quantities:
                        row.update({quantity: curve.get(quantity)})

                    df_jv.loc[len(df_jv.index)] = row
                    #print(row)
    df_q = df_q.set_index("entry_id")
    df_jv = df_jv.set_index("entry_id")

    df = df_q.merge(df_jv, on="entry_id")
    
    return df



def get_specific_data_of_sample(sample_id, entry_type, nomad_url, token, with_meta=False):
    # collect the results of the sample, in this case it are all the annealing temperatures
    entry_id = get_entryid(sample_id, nomad_url, token)

    query = {
        'required': {
            'metadata': '*',
            'data': '*',
        },
        'owner': 'visible',
        'query': {'entry_references.target_entry_id': entry_id},
        'pagination': {
            'page_size': 100
        }
    }
    response = requests.post(f'{nomad_url}/entries/archive/query',
                             headers={'Authorization': f'Bearer {token}'}, json=query)
    linked_data = response.json()["data"]
    res = []

    for ldata in linked_data:
        if entry_type not in ldata["archive"]["metadata"]["entry_type"]:
            continue
        if with_meta:
            res.append((ldata["archive"]["data"],ldata["archive"]["metadata"]))
        else:
            res.append(ldata["archive"]["data"])
    return res
