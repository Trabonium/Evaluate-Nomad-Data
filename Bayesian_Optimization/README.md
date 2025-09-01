# How to use:

## NOMAD credentials
include your nomad username and password under '\bayesian-optimization\conf\local\credentials.yml' in the following format:
```
nomad_db:
  username: <your-username>
  password: <your-password>
```

This will not be committed to version control.

## BO Pipeline
### Pipeline execution

Put your ELN Excel file in '\bayesian-optimization\data\01_raw\'

Check that the ELN file name matches experiment_ids in '\bayesian-optimization\conf\local\catalog.yml', if not change the catalog file path.

Open console, ensure that the virtual environment is running, change folder to 'Bayesian_Optimization\bayesian-optimization' and execute 'kedro run'

### Outputs
The BO pipeline will produce 3 output files:
The suggested experimentation parameters in '\bayesian-optimization\data\07_model_output\'
Two graphs in '\bayesian-optimization\data\08_reporting\' for the exploration and exploitation focused models.

### WIP: Changing model parameters

## BOinitCube
Needs nomad credentials and an Excel file with batch data in '\bayesian-optimization\data\01_raw\'