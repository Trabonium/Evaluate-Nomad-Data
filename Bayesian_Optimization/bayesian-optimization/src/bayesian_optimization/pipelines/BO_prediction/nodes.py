import pandas as pd

def get_data_from_DB(experiment_ids: pd.DataFrame) -> pd.DataFrame:
    #get the experiment data from NOMAD db and add it to the df
    pass


def preprocess_data(experiment_data: pd.DataFrame) -> pd.DataFrame:
    #convert 
    pass

def make_prediction(data: pd.DataFrame):
    #core Bayesian optimization implementation
    pass