"""
This is a boilerplate pipeline 'multiobj_BO'
generated using Kedro 0.19.13
"""

from kedro.pipeline import node, Pipeline, pipeline  # noqa
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
                outputs=["preprocessed_data","preprocessed_data_minimization"],
                name="preprocess_data"
            ),
            node(
                func=mobo_predict,
                inputs=["preprocessed_data","preprocessed_data_minimization"],
                outputs="mobo_prediction",
                name="mobo_predict"
            )
        ]
    )
