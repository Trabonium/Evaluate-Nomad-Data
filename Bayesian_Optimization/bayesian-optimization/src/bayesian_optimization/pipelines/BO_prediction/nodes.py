import pandas as pd
import os, sys, requests

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..", "..")))

from kedro.config import OmegaConfigLoader
from kedro.framework.project import settings
from pathlib import Path
from functions.api_calls_get_data import get_entryid

def get_data_from_DB(experiment_ids: pd.DataFrame) -> pd.DataFrame:
    #get the experiment data from NOMAD db and add it to the df
    
    #load credentials from local config
    kedro_root = Path(__file__).parent.parent.parent.parent.parent
    path_to_credentials =  str(kedro_root) + "\\conf"
    conf_loader = OmegaConfigLoader(conf_source=path_to_credentials)
    credentials = conf_loader["credentials"]
    nomad_user = credentials['nomad_db']['username']
    nomad_pw = credentials['nomad_db']['password']
    #get access token with credentials
    nomad_url = "http://elnserver.lti.kit.edu/nomad-oasis/api/v1"
    global token
    try:
        response = requests.get(f"{nomad_url}/auth/token", params={"username": nomad_user, "password": nomad_pw})
        response.raise_for_status()
        token = response.json().get('access_token', None)
        print("Login successful.", f"Logged in as {nomad_user}")
    except requests.exceptions.RequestException as e:
        print("Login Failed", f"Error: {e}")
        exit
    
    #drop any lines where Nomad ID is not set
    experiment_ids.dropna(how='any', subset='Nomad ID', inplace=True)
    sample_ids = list(experiment_ids['Nomad ID'])

    #query the entry id from the main page
    query = {
        'required': {
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
    with_id = pd.DataFrame(data=data)

    #get remaining pages
    while (response['pagination'].get('next_page_after_value')):
        next_page = response['pagination'].get('next_page_after_value')
        query['pagination']['page_after_value'] = next_page
        response = requests.post(
        f'{nomad_url}/entries/query', headers={'Authorization': f'Bearer {token}'}, json=query).json()
        data = response['data']
        with_id = pd.concat([with_id, pd.DataFrame(data)], ignore_index=True)
    
    experiment_ids = experiment_ids.rename(columns={'Nomad ID': 'entry_name'})
    experiment_ids = experiment_ids.join(with_id.set_index('entry_name'), on='entry_name')
    id_list = list(experiment_ids['entry_id'])

    #get the step parameters from entries referencing the entry ids
    query = {'required': {
        'metadata': {'entry_references': '*'},
        'data': {'positon_in_experimental_plan': '*', 'recipe_steps': '*', 'quenching': '*'},
        },'owner': 'visible',
        'query':{
            'entry_references.target_entry_id':{'any': id_list},
            'entry_type': 'peroTF_SpinCoating',
            #'archive': {'data': {'positon_in_experimental_plan': '3.0'}}
        },
        'pagination': {'page_size': 100}}

    response = requests.post(
        f'{nomad_url}/entries/archive/query', headers={'Authorization': f'Bearer {token}'}, json=query).json()

    step_data = []
    for entry in response['data']:
        #the data we are looking for is in the 3rd step
        if (entry['archive']['data']['positon_in_experimental_plan'] != 3.0):
            continue
        try:
            rota_time_2 = entry['archive']['data']['recipe_steps'][1]['time']
            dropping_time = entry['archive']['data']['quenching']['anti_solvent_dropping_time']
            #dropping_speed = entry['archive']['data']['quenching']['anti_solvent_dropping_flow_rate']
        except KeyError:
            #if one of these values is missing, the samples using this step can't be used
            continue
        for referenced_sample in entry['archive']['metadata']['entry_references']:
            step_data.append([referenced_sample['target_entry_id'], rota_time_2, dropping_time])

    #get remaining pages
    while (response['pagination'].get('next_page_after_value')):
        next_page = response['pagination'].get('next_page_after_value')
        query['pagination']['page_after_value'] = next_page
        response = requests.post(
        f'{nomad_url}/entries/archive/query', headers={'Authorization': f'Bearer {token}'}, json=query).json()
        for entry in response['data']:
            #the data we are looking for is in the 3rd step
            if (entry['archive']['data']['positon_in_experimental_plan'] != 3.0):
                continue
            try:
                rota_time_2 = entry['archive']['data']['recipe_steps'][1]['time']
                dropping_time = entry['archive']['data']['quenching']['anti_solvent_dropping_time']
                #dropping speed is currently missing in the database
                #dropping_speed = entry['archive']['data']['quenching']['anti_solvent_dropping_flow_rate']
            except KeyError:
                #if one of these values is missing, the samples using this step can't be used
                continue
            for referenced_sample in entry['archive']['metadata']['entry_references']:
                step_data.append([referenced_sample['target_entry_id'], rota_time_2, dropping_time])

    #join the queried step parameters on the entry ids in the main Dataframe
    step_data_df = pd.DataFrame(data=step_data, columns=['entry_id', 'rotation_time_2', 'dropping_time'])
    step_data_df = step_data_df.drop_duplicates()
    experiment_ids = experiment_ids.join(step_data_df.set_index('entry_id'), on='entry_id', validate='1:1')

    #get efficiency from pixel measurements
    
    query = {'required': {
        'data': {'name': '*', 'jv_curve': '*'}
        },'owner': 'visible',
        'query':{
            'entry_references.target_entry_id':{'any': id_list},
            'entry_type': 'peroTF_JVmeasurement',
        },
        'pagination': {'page_size': 100}}
    next_page = 'dummy_enter_once'
    efficiencies = []

    #execute DB query and fetch all pages
    while(next_page):
        if(next_page == 'dummy_enter_once'):
            next_page = None
        else:
            query['pagination']['page_after_value'] = next_page
    

        response = requests.post(
            f'{nomad_url}/entries/archive/query', headers={'Authorization': f'Bearer {token}'}, json=query).json()
        
        for entry in response['data']:
            try:
                entry_name, pixel = entry['archive']['data']['name'].split()
                efficiency_backward = entry['archive']['data']['jv_curve'][0]['efficiency']
                efficiency_forward = entry['archive']['data']['jv_curve'][1]['efficiency']
                efficiencies.append([entry_name, pixel, efficiency_backward, efficiency_forward])
            except KeyError:
                #one of the data points is missing, so instead of initializing it as None and dropping it later, it is skipped here
                continue
        
        next_page = response['pagination'].get('next_page_after_value')
    
    pixel_data = pd.DataFrame(data=efficiencies, columns=['entry_name', 'pixel', 'efficiency_backward', 'efficiency_forward'])
    experiment_ids = experiment_ids.join(pixel_data.set_index('entry_name'), on='entry_name', validate='1:m')
    experiment_ids = experiment_ids.reset_index()

    return experiment_ids


def preprocess_data(experiment_data: pd.DataFrame) -> pd.DataFrame:
    #convert data types, clean data and create new columns that are entirely predecated on existing columns
    #rename columns
    experiment_data = experiment_data.rename(columns={'Anti solvent dropping speed [uL/s]': 'dropping_speed'})
    
    #convert column types into more fitting ones
    experiment_data['Date'] = experiment_data['Date'].apply(lambda x: pd.to_datetime(x, format='%Y%m%d'))
    experiment_data = experiment_data.astype(dtype={'Sample': int, 'Subbatch': int})


    rotation_time_before = 10
    experiment_data['time_after'] = rotation_time_before + experiment_data['rotation_time_2'] - experiment_data['dropping_time']
    
    experiment_data.dropna(how='any', subset=['dropping_speed', 'time_after', 'dropping_time', 'efficiency_forward', 'efficiency_backward'], inplace=True)
    return experiment_data

def make_prediction(data: pd.DataFrame):
    #core Bayesian optimization implementation
    
    pass