"""Project pipelines."""

from kedro.pipeline import Pipeline

import bayesian_optimization.pipelines.BO_prediction as singleBO
import bayesian_optimization.pipelines.multiobj_BO as mobo

def register_pipelines() -> dict[str, Pipeline]:
    """Register the project's pipelines.

    Returns:
        A mapping from pipeline names to ``Pipeline`` objects.
    """
    single_BO_pipeline = singleBO.create_pipeline()
    mobo_pipeline = mobo.create_pipeline()
    pipelines = {"__default__": single_BO_pipeline,
                 "singleBO": single_BO_pipeline,
                 "mobo": mobo_pipeline
                }
    return pipelines
