import pandas as pd
import os, sys, requests, logging, math

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..", "..")))

from kedro.config import OmegaConfigLoader
from kedro.framework.project import settings
from pathlib import Path
from bayes_opt import BayesianOptimization, acquisition
from functions.api_calls_get_data import get_entryid

logger = logging.getLogger(__name__)

#bounds suggested by Daniel
#all input parameters must be specified here
BOUNDS = {'dropping_time': (20, 44),'time_after': (1, 25), 'dropping_speed': (25, 1000)}

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

def _normalize_columns(df: pd.DataFrame, normalization_bounds: dict):
    for label in normalization_bounds:
        if not df.columns.__contains__(label):
            logger.error(f'Column {label} was specified in bounds but is not present in the dataframe!')
            return df
        df[label] = (df[label] - normalization_bounds[label][0]) / (normalization_bounds[label][1] - normalization_bounds[label][0])

    return df

def _denormalize_columns(df: pd.DataFrame, normalization_bounds: dict):
    for label in normalization_bounds:
        if not df.columns.__contains__(label):
            logger.error(f'Column {label} was specified in bounds but is not present in the dataframe!')
            return df
        df[label] = (df[label] * (normalization_bounds[label][1] - normalization_bounds[label][0])) + normalization_bounds[label][0]
    
    return df

def preprocess_data(experiment_data: pd.DataFrame) -> pd.DataFrame:
    #convert data types, clean data and create new columns that are entirely predecated on existing columns
    #rename columns
    experiment_data = experiment_data.rename(columns={'Anti solvent dropping speed [uL/s]': 'dropping_speed'})
    
    #convert column types into more fitting ones
    experiment_data['Date'] = experiment_data['Date'].apply(lambda x: pd.to_datetime(x, format='%Y%m%d'))
    experiment_data = experiment_data.astype(dtype={'Sample': int, 'Subbatch': int})


    rotation_time_before = 10
    experiment_data['time_after'] = rotation_time_before + experiment_data['rotation_time_2'] - experiment_data['dropping_time']

    experiment_data['mean_efficiency'] = (experiment_data['efficiency_forward'] + experiment_data['efficiency_backward']) /200
    
    experiment_data.dropna(how='any', subset=['dropping_speed', 'time_after', 'dropping_time', 'efficiency_forward', 'efficiency_backward'], inplace=True)

    #normalize input parameters
    experiment_data = _normalize_columns(experiment_data, BOUNDS)

    return experiment_data

def _get_suggestion(optimizer: BayesianOptimization) -> dict[str, float]:
    suggestion = optimizer.suggest()
    #check constraints and get a new value if the suggestion is out of bounds along with registering a dummy bad data point at the suggested, out of bounds point
    suggestion_denormalized = _denormalize_columns(pd.DataFrame(data=suggestion, index=range(1)), normalization_bounds=BOUNDS)
    if (suggestion_denormalized['time_after'][0] + suggestion_denormalized['dropping_time'][0] > 45):
        optimizer.register(params=suggestion, target=0.0)
        suggestion_string = ""
        for c in suggestion_denormalized.columns: suggestion_string += c + "=" + str(suggestion_denormalized[c][0]) + "; "
        logger.info(f'optimizer suggested {suggestion_string}which is outside the constrained space. Inserted dummy point with 0.0 efficiency.')
        #recursive call because the next suggestion could also be out of bounds
        suggestion = _get_suggestion(optimizer)
    
    return suggestion

def _calculate_min_distance(points: pd.DataFrame, minimum_relative_distance: float):
    """calculates the minimum distance between each point and its nearest neighbour
        points: dataframe of points (rows) with their dimensions (columns). Dimensions must be float or int.
        bounds: dict with a pair of values bounding each dimension of the points. Must be named the same as the points columns.
        minimum_relative distance: Value ranging from 0.0 to sqrt(dimensions of the points) which when undercut will cause a warning.
    """
     
    minimum_distances = []
    for index, row in points.iterrows():
        distances = []
        for index2, row2 in points.iterrows():
            if index == index2:
                #the point is being compared to itself
                continue
            curr_distance = 0.0
            for column in range(row.size):
                curr_distance += math.pow((row.iloc[column] - row2.iloc[column]), 2)
            curr_distance = math.sqrt(curr_distance)
            distances.append(curr_distance)
        minimum_distances.append(min(distances))

    global_min_distance = min(minimum_distances)
    
    if (global_min_distance < minimum_relative_distance):
        logger.warning(f'the minimum distance calculated was {round(global_min_distance*100, 2)}%, which is below the specified minimum distance of {minimum_relative_distance*100}%')
    else:
        logger.info(f'minimum distance was calculated to be {round(global_min_distance*100, 2)}%')
    return(global_min_distance)



def make_prediction(data: pd.DataFrame):
    #core Bayesian optimization implementation    
        
    trivial_normalized_bounds = {'dropping_time': (0, 1),'time_after': (0, 1), 'dropping_speed': (0, 1)}
    #optimizer focused on exploitation: Mostly looks for highest improvement
    acq_fn_exploitation = acquisition.ExpectedImprovement(xi=0.0, random_state=1)
    optimizer_exploitation = BayesianOptimization(f=None, acquisition_function=acq_fn_exploitation, pbounds=trivial_normalized_bounds, verbose=2, random_state=1, allow_duplicate_points=True)
    optimizer_exploitation.set_gp_params(alpha=1e-4)

    #second optimizer focused on exploration
    acq_fn_exploration = acquisition.ExpectedImprovement(xi=0.1, random_state=1)
    optimizer_exploration = BayesianOptimization(f=None, acquisition_function=acq_fn_exploration, pbounds=trivial_normalized_bounds, verbose=2, random_state=1, allow_duplicate_points=True)
    optimizer_exploration.set_gp_params(alpha=1e-4)
    """for i in range(0,100):
        sug_exploitation = optimizer_exploitation.suggest()
        target_exploitation = dumbest_function(**sug_exploitation)
        sug_exploration = optimizer_exploration.suggest()
        target_exploration = dumbest_function(**sug_exploration)
        optimizer_exploitation.register(params=sug_exploitation, target=target_exploitation)
        optimizer_exploration.register(params=sug_exploitation, target=target_exploitation)
        optimizer_exploitation.register(params=sug_exploration, target=target_exploration)
        optimizer_exploration.register(params=sug_exploration, target=target_exploration)
        print(f"suggestion exploit: {sug_exploitation}, result: {target_exploitation}")
        print(f"suggestion explore: {sug_exploration}, result: {target_exploration}")
        print("Both points registered.")"""
    for index, row in data.iterrows():
        parameters = {
            'dropping_time': row['dropping_time'],
            'time_after': row['time_after'],
            'dropping_speed': row['dropping_speed']
        }
        target = row['mean_efficiency']

        optimizer_exploitation.register(params=parameters, target=target)
        optimizer_exploration.register(params=parameters, target=target)

    suggestion_exploitation = _get_suggestion(optimizer_exploitation)
    suggestion_exploitation['method'] = 'exploitation'
    suggestion_exploitation_2 = _get_suggestion(optimizer_exploitation)
    suggestion_exploitation_2['method'] = 'exploitation'
    suggestion_exploration = _get_suggestion(optimizer_exploration)
    suggestion_exploration['method'] = 'exploration'
    suggestion_exploration_2 = _get_suggestion(optimizer_exploration)
    suggestion_exploration_2['method'] = 'exploration'
    
    suggestions = pd.DataFrame(data=[suggestion_exploitation, suggestion_exploitation_2, suggestion_exploration, suggestion_exploration_2])
    _calculate_min_distance(suggestions.drop(labels={'method'}, axis=1, inplace=False), 0.01)
    suggestions = _denormalize_columns(suggestions, BOUNDS)
    suggestions = suggestions.round(2)
    return suggestions