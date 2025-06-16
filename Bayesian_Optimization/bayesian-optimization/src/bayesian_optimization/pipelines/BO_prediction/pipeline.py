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
                outputs=["prediction", "optimizer_1", "optimizer_2"],
                name="make_prediction"
            ),
            node(
                func=visualize,
                inputs="optimizer_1",
                outputs="dimension_stacking_plot_1",
                name="visualize_exploitation_opt"
            ),
            node(
                func=visualize,
                inputs="optimizer_2",
                outputs="dimension_stacking_plot_2",
                name="visualize_exploration_opt"
            )
        ]
    )
