## How to use:
include your nomad username and password under '\bayesian-optimization\conf\local\credentials.yml' in the following format:
```
nomad_db:
  username: <your-username>
  password: <your-password>
```

This will not be committed to version control.

### BOinitCube
Needs nomad credentials and an Excel file with batch data in '\bayesian-optimization\data\01_raw\'