#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""

"""

import requests
import pandas as pd
import numpy as np


def get_entryid(sample_id, nomad_url, token):  # give it a batch id
    # get all entries related to this batch id
    query = {
        'required': {
            'metadata': '*'
        },
        'owner': 'visible',
        'query': {'results.eln.lab_ids': sample_id},
        'pagination': {
            'page_size': 100
        }
    }
    response = requests.post(
        f'{nomad_url}/entries/query', headers={'Authorization': f'Bearer {token}'}, json=query)
    data = response.json()["data"]
    assert len(data) == 1
    return data[0]["entry_id"]


def return_value(data, path):
    if path:
        try:
            return return_value(data[int(path[0])], path[1:])
        except:
            return return_value(data[path[0]],  path[1:])
    return data


def get_quantity_over_jv(samples_of_batch, key_1, quantities,  jv_quantities, nomad_url, token):
    if not isinstance(key_1, list):
        key_1 = [key_1]
    # collect the results of the sample, in this case it are all the annealing temperatures
    df_q = pd.DataFrame(columns=["entry_id","sample_id"]+quantities)
    df_jv = pd.DataFrame(columns=["entry_id"]+jv_quantities)

    for sample_ids in samples_of_batch:
        sample_id = sample_ids[1]
        row = {"entry_id": sample_id, "sample_id":sample_ids[0]}
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
            if any([kk in link["archive"]["metadata"]["entry_type"] for kk in key_1]):
                data = link["archive"]["data"]
                for q in quantities:
                    q_split = q.split("/")

                    row.update({q: return_value(data.copy(), q_split.copy())})

        df_q.loc[len(df_q.index)] = row
        for link in linked_data:
            if "JVmeasurement" in link["archive"]["metadata"]["entry_type"]:
                row = {"entry_id": sample_id}
                for curve in link["archive"]["data"]["jv_curve"]:
                    for quantity in jv_quantities:
                        row.update({quantity: curve.get(quantity)})

                    df_jv.loc[len(df_jv.index)] = row
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
