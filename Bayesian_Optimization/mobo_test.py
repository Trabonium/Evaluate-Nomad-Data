import torch

from botorch.models import SingleTaskGP
from botorch.acquisition.multi_objective.max_value_entropy_search import (
    qLowerBoundMultiObjectiveMaxValueEntropySearch,
)
from botorch.utils.multi_objective.box_decompositions import NondominatedPartitioning
from botorch.optim import optimize_acqf
from botorch.fit import fit_gpytorch_mll
from gpytorch.mlls import ExactMarginalLogLikelihood
from botorch.utils.multi_objective.pareto import is_non_dominated

torch.manual_seed(0)
dtype = torch.double

"""# 3D input, N = 6 points
train_X = torch.tensor(
    [
        [0.1, 0.2, 0.3],
        [0.1, 0.2, 0.3],  # duplicate X (experimental noise)
        [0.4, 0.5, 0.6],
        [0.7, 0.8, 0.9],
        [0.2, 0.4, 0.6],
        [0.9, 0.1, 0.3],
    ],
    dtype=dtype,
)

# Two objectives, lower is better
train_Y = torch.tensor(
    [
        [-10.0, -5.0],
        [-11.0, -6.0],
        [-7.0, -3.0],
        [-4.0, -2.0],
        [-8.0, -4.0],
        [-6.0, -1.0],
    ],
    dtype=dtype,
)"""

train_X = torch.tensor([
        [0],
        [0.4],
        [0.5],
        [0.6],
        [1]
    ],dtype=dtype)
train_Y = torch.tensor([
    [100,90],
    [20,40],
    [25,25],
    [40,20],
    [90,100]
],dtype=dtype)

train_Y_max = -1 * train_Y
model = SingleTaskGP(train_X, train_Y)
mll = ExactMarginalLogLikelihood(model.likelihood, model)
fit_gpytorch_mll(mll)

model.eval()

# Reference point (slightly worse than worst observed value)
# NondominatedPartitioning assumes maximization
margin = 1.0
ref_point = train_Y_max.min(dim=0).values - margin

partitioning = NondominatedPartitioning(
    ref_point=ref_point,
    Y=train_Y_max,
)

"""# Shape: 2 x num_boxes x num_objectives
hb = partitioning.get_hypercell_bounds()

# Add num_pareto_samples dimension
# Final shape: 1 x 2 x num_boxes x num_objectives
hypercell_bounds = hb.unsqueeze(0)"""

# observed objective range
y_min = train_Y.min(dim=0).values
y_max = train_Y.max(dim=0).values

# finite upper cap (slightly worse than worst observed)
upper_cap = y_max + 1.0

# one pareto sample, one box, two objectives
hypercell_bounds = torch.tensor(
    [[
        [y_min.tolist()],     # lower bounds
        [upper_cap.tolist()]  # upper bounds
    ]],
    dtype=train_Y.dtype,
)

assert torch.isfinite(hypercell_bounds).all()

acq_func = qLowerBoundMultiObjectiveMaxValueEntropySearch(
    model=model,
    hypercell_bounds=hypercell_bounds,
    estimation_type="LB",
    num_samples=64,
)

bounds = torch.tensor(
    [[0.0],
     [1.0]],
    dtype=dtype,
)

candidate, acquisition_value = optimize_acqf(
    acq_function=acq_func,
    bounds=bounds,
    q=1,
    num_restarts=20,
    raw_samples=256,
    sequential=True,
)

predicted_value =  model.posterior(candidate).mean

pareto_Y = -1 * partitioning.pareto_Y
pareto_mask = is_non_dominated(train_Y_max)
pareto_X = train_X[pareto_mask]

print("Candidate:", candidate)
print("Predicted objective values:", predicted_value)
print("Pareto X:", pareto_X)
print("Pareto_Y:", pareto_Y)
