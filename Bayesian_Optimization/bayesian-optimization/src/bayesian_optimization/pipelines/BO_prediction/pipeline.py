from kedro.pipeline import node, Pipeline, pipeline
from .nodes import *

def create_pipeline(**kwargs) -> Pipeline:
    return pipeline(
        [
            node(
                func=get_data_from_DB,
                inputs="experiment_ids",
                outputs="complete_data",
                name="get_data_from_DB"
            ),
            node(
                func=preprocess_data,
                inputs="complete_data",
                outputs="preprocessed_data",
                name="preprocess_data"
            ),
            node(
                func=make_prediction,
                inputs="preprocessed_data",
                outputs="prediction",
                name="make_prediction"
            )
        ]
    )
