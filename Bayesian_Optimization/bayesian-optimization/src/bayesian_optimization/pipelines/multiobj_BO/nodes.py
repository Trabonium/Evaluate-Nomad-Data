
import pandas as pd
import numpy as np
import os, sys, requests, logging
import torch

from kedro.config import OmegaConfigLoader
from kedro.framework.project import settings
from pathlib import Path
from botorch.acquisition.multi_objective.max_value_entropy_search import qLowerBoundMultiObjectiveMaxValueEntropySearch
from botorch.models import SingleTaskGP
from botorch.models.transforms import Standardize
from botorch.optim import optimize_acqf
from botorch.utils.multi_objective.pareto import is_non_dominated
from ..BO_prediction.nodes import _normalize_columns


logger = logging.getLogger(__name__)

#bounds suggested by Daniel
#all input parameters must be specified here
BOUNDS = {'dropping_speed': (25, 1000),'dropping_time': (20, 40),'rotation_time_2': (11, 35)}

#Champion mode reduces the input data to only the best PCE result for each unique set of experiment settings
CHAMPION_MODE = True

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
        response = requests.post(f"{nomad_url}/auth/token", params={"username": nomad_user, "password": nomad_pw})
        response.raise_for_status()
        token = response.json().get('access_token', None)
        logger.info(f"Login successful. Logged in as {nomad_user}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Login Failed. Error: {e}")
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
                jsc_backward = entry['archive']['data']['jv_curve'][0]['short_circuit_current_density']
                jsc_forward = entry['archive']['data']['jv_curve'][1]['short_circuit_current_density']
                efficiencies.append([entry_name, pixel, efficiency_backward, efficiency_forward, jsc_backward, jsc_forward])
            except KeyError:
                #one of the data points is missing, so instead of initializing it as None and dropping it later, it is skipped here
                continue
        
        next_page = response['pagination'].get('next_page_after_value')
    
    pixel_data = pd.DataFrame(data=efficiencies, columns=['entry_name', 'pixel', 'efficiency_backward', 'efficiency_forward', 'jsc_backward', 'jsc_forward'])
    experiment_ids = experiment_ids.join(pixel_data.set_index('entry_name'), on='entry_name', validate='1:m')
    experiment_ids = experiment_ids.reset_index()

    return experiment_ids

def preprocess_data(experiment_data: pd.DataFrame) -> pd.DataFrame:
    #convert data types, clean data and create new columns that are entirely predecated on existing columns
    #rename columns
    experiment_data = experiment_data.rename(columns={'Anti solvent dropping speed [uL/s]': 'dropping_speed'})
    
    #convert column types into more fitting ones
    experiment_data['Date'] = experiment_data['Date'].apply(lambda x: pd.to_datetime(x, format='%Y%m%d'))


    rotation_time_before = 10
    experiment_data['time_after'] = rotation_time_before + experiment_data['rotation_time_2'] - experiment_data['dropping_time']

    experiment_data['mean_efficiency'] = (experiment_data['efficiency_forward'] + experiment_data['efficiency_backward']) /200
    experiment_data['mean_jsc'] = (experiment_data['jsc_forward'] + experiment_data['jsc_backward']) /2
    
    experiment_data.dropna(how='any', subset=['dropping_speed', 'time_after', 'dropping_time', 'efficiency_forward', 'efficiency_backward'], inplace=True)

    #normalize input parameters
    experiment_data = _normalize_columns(experiment_data, BOUNDS)

    if CHAMPION_MODE:
        idx = (
            experiment_data
                .groupby(list(BOUNDS.keys()))["mean_efficiency"]
                .idxmax()
            )
        experiment_data = experiment_data.loc[idx].reset_index(drop=True)

    FACTOR_TO_KEEP = 1
    if (FACTOR_TO_KEEP<1):
        rowcount = len(experiment_data)
        experiment_data = experiment_data.head(int(rowcount*FACTOR_TO_KEEP))

    #invert efficiency values to accomodate minimization of BO algorithm
    experiment_data_MIN = experiment_data.copy()
    experiment_data_MIN[['efficiency_forward', 'efficiency_backward']] = experiment_data_MIN[['efficiency_forward', 'efficiency_backward']] * -1

    return experiment_data, experiment_data_MIN

def _format_tensor(t):
    return np.array2string(t.detach().cpu().numpy(), separator=", ")

def _denormalize_single_set(values: list, normalization_bounds: list) -> list:
    """denormalizes a single value vector according to bounds (2d array). Values must have the same size as normalization_bounds and is assumed to be in the same order."""
    if (len(values) != len(normalization_bounds)):
        logger.error(f'During denormalization, two lists of different lengths were specified to denormalize.')
        return None
    denormalized = []
    for x in range(len(values)):
        denormalized.append((values[x] * (normalization_bounds[x][1] - normalization_bounds[x][0])) + normalization_bounds[x][0])
    return denormalized
    

def mobo_predict(data_maximization: pd.DataFrame, data_minimization: pd.DataFrame):
    
    #take only relevant columns and convert them to torch usable format
    train_input = torch.tensor(data_minimization[BOUNDS.keys()].to_numpy(), dtype=torch.double)
    train_values = torch.tensor(data_minimization[['efficiency_forward', 'efficiency_backward']].to_numpy(), dtype=torch.double)
    train_values_maximization = torch.tensor(data_maximization[['efficiency_forward', 'efficiency_backward']].to_numpy(), dtype=torch.double)
    
    #initialize model
    y_transform = Standardize(train_values.shape[-1])
    model = SingleTaskGP(
        train_X=train_input,
        train_Y=train_values,
        input_transform=None, #input was already normalized before
        outcome_transform=Standardize(train_values.shape[-1])
    )
    model.eval()

    #calculate hypercell bounds from output values
    
    # observed objective range
    y_min = train_values.min(dim=0).values
    y_max = train_values.max(dim=0).values

    # upper cap (slightly worse than worst observed)
    upper_cap = y_max + 1.0

    hypercell_bounds = torch.tensor(
        [[
            [y_min.tolist()],     # lower bounds
            [upper_cap.tolist()]  # upper bounds
        ]],
        dtype=train_values.dtype,
    )
    assert torch.isfinite(hypercell_bounds).all()

    #initialize acquisition function
    acq_func = qLowerBoundMultiObjectiveMaxValueEntropySearch(
        model=model,
        hypercell_bounds=hypercell_bounds,
        X_pending=None,
    )

    normalized_bounds = torch.tensor([[0.,0.,0.],[1.,1.,1.]], dtype=torch.double)

    candidate, acquisition_value = optimize_acqf(
        acq_function=acq_func,
        bounds=normalized_bounds,
        q=1,
        num_restarts=30,
        raw_samples=512,
        sequential=True
    )
    candidate_denorm = _denormalize_single_set(candidate.tolist()[0], list(BOUNDS.values()))
    

    nd_mask = is_non_dominated(train_values_maximization)
    pareto_X = train_input[nd_mask]
    pareto_Y = train_values[nd_mask]

    #Pareto Y is from min space
    pareto_Y *= -1

    predicted_value =  model.posterior(candidate).mean

    #prepare output file
    text_output = []

    text_output.append("=== Multiobjective BO Iteration Summary ===\n")

    text_output.append("--- Input Settings: ---\n")

    text_output.append("Bounds:")
    text_output.append(str(BOUNDS))

    text_output.append("\nChampion Mode:")
    text_output.append(str(CHAMPION_MODE))

    text_output.append("\n--- Output: ---")

    text_output.append("\nPareto Front (X):")
    text_output.append(_format_tensor(pareto_X))
    text_output.append("\nPareto Front (Y):")
    text_output.append(_format_tensor(pareto_Y))

    text_output.append("\nHypercell Bounds:")
    text_output.append(_format_tensor(hypercell_bounds*-1))

    text_output.append("\nSelected Candidate Point:")
    text_output.append(str(candidate_denorm))

    text_output.append("\nPredicted Value at Candidate:")
    text_output.append(_format_tensor(predicted_value*-1))

    text_output = "\n".join(text_output)

    return text_output