#need to import from 1 folder above, so I add .. to sys path
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from kedro.config import OmegaConfigLoader
from kedro.framework.project import settings

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import requests
from functions.get_data import get_data_excel_to_df

# Define cube limits
time_range = (22, 40)
speed_range = (25, 1000)
time_after_range = (1, 23)

# Normalize cube size for visualization
def normalize(value, vmin, vmax):
    return (value - vmin) / (vmax - vmin)

# Define cube vertices (normalized for display)
cube_vertices = np.array([
    [time_range[0], speed_range[0], time_after_range[0]],
    [time_range[0], speed_range[0], time_after_range[1]],
    [time_range[0], speed_range[1], time_after_range[0]],
    [time_range[0], speed_range[1], time_after_range[1]],
    [time_range[1], speed_range[0], time_after_range[0]],
    [time_range[1], speed_range[0], time_after_range[1]],
    [time_range[1], speed_range[1], time_after_range[0]],
    [time_range[1], speed_range[1], time_after_range[1]],
])

# Normalize for equal aspect ratio in visualization
cube_vertices_norm = np.array([
    [normalize(x, *time_range), normalize(y, *speed_range), normalize(z, *time_after_range)]
    for x, y, z in cube_vertices
])

# Define cube faces
faces = [
    [cube_vertices_norm[i] for i in [0, 1, 3, 2]],  # Front face
    [cube_vertices_norm[i] for i in [4, 5, 7, 6]],  # Back face
    [cube_vertices_norm[i] for i in [0, 1, 5, 4]],  # Left face
    [cube_vertices_norm[i] for i in [2, 3, 7, 6]],  # Right face
    [cube_vertices_norm[i] for i in [0, 2, 6, 4]],  # Bottom face
    [cube_vertices_norm[i] for i in [1, 3, 7, 5]],  # Top face
]

# Create figure
fig = plt.figure(figsize=(8, 8))
ax = fig.add_subplot(111, projection='3d')

# Plot cube
ax.add_collection3d(Poly3DCollection(faces, facecolors='grey', linewidths=1, edgecolors='k', alpha=0.1))

# Labels
ax.set_xlabel("Time (22-40)")
ax.set_ylabel("Speed (25-1000)")
ax.set_zlabel("Time After (1-23)")

# Formatting axis limits (normalized)
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.set_zlim(0, 1)

# Function to plot points
def plot_point(time, speed, time_after, color='red'):
    x = normalize(time, *time_range)
    y = normalize(speed, *speed_range)
    z = normalize(time_after, *time_after_range)
    
    # Check if the point is in the forbidden region
    if time + time_after < 45:
        print(f"Warning: Point ({time}, {speed}, {time_after}) is in the forbidden region!")
    
    ax.scatter(x, y, z, color=color, s=100, edgecolors='k')

# Example: Add points
"""plot_point(25, 200, 10, '#FFFFFF')
plot_point(23.2, 125, 11.8, 'orange')
plot_point(23.2, 900, 11.8, 'orange')
plot_point(32.8, 125, 2.2, 'orange')
plot_point(32.8, 900, 2.2, 'orange')
plot_point(24.2, 125, 20.8, 'blue')
plot_point(24.2, 900, 20.8, 'blue')
plot_point(40, 125, 5, 'blue')
plot_point(40, 900, 5, 'blue')
plot_point(27.4, 515, 12, 'green')
plot_point(31, 320, 12, 'green')
plot_point(31, 710, 12, 'green')
plot_point(34.6, 515, 10.4, 'green')
plot_point(34.6, 515, 10.4, 'green')
plot_point(31, 515, 7.6, 'yellow')
plot_point(23.8, 515, 2.2, 'yellow')
plot_point(38.2, 515, 2.2, 'yellow')
plot_point(22, 515, 7.6, 'yellow')
plot_point(25, 50, 10, 'purple')
plot_point(25, 350, 10, 'purple')
plot_point(25, 200, 13.3, 'purple')
plot_point(25, 200, 6.7, 'purple')"""

#load credentials from credentials.yml in kedro conf
path_to_credentials = os.path.dirname(os.path.abspath(sys.argv[0])) + "\\bayesian-optimization\\conf"
conf_loader = OmegaConfigLoader(conf_source=path_to_credentials)
credentials = conf_loader["credentials"]
nomad_user = credentials['nomad_db']['username']
nomad_pw = credentials['nomad_db']['password']

path_to_excel = "C:/Users/hr0264/Documents/901_ELN/Evaluate-Nomad-Data/Bayesian_Optimization/bayesian-optimization/data/01_raw/_KIT_DaBa_BO_ExPlan.xlsx"
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

data = get_data_excel_to_df(path_to_excel, nomad_url, token)

#add time_after column
rotation_time_before = 10
data['time_after'] = rotation_time_before + data['rotation_time'] - data['dropping_time']

max_efficiency = data['efficiency'].max()
min_efficiency = data['efficiency'].min()

def get_gradient_color(efficiency: float, max: float, min: float) -> str:
    color_max = [0xFF, 0xAA, 0] #RGB yellow
    color_min = [0, 0, 0xAA] #RGB blue
    color = "#"
    for i in range(3):
        x = efficiency * (color_max[i] - color_min[i]) / (max - min)
        x += color_min[i]
        color += f"{int(x):02X}"

    return color


current_max = data.loc[0]
for index, row in data.iterrows():
    if row['variation'] == current_max['variation']:
        if row['efficiency'] > current_max['efficiency']:
            current_max = row
    else:
        color = get_gradient_color(current_max['efficiency'], max_efficiency, min_efficiency)
        plot_point(current_max['dropping_time'], current_max['dropping_speed'], current_max['time_after'], color=color)
        current_max = row
    



# --- Plot the constraint line in the X-Z plane ---
time_values = np.linspace(time_range[0], time_range[1], 100)
time_after_values = 45 - time_values  # Constraint: time + time_after = 45

# Keep only values inside the allowed range
valid_indices = (time_after_values >= time_after_range[0]) & (time_after_values <= time_after_range[1])
time_values = time_values[valid_indices]
time_after_values = time_after_values[valid_indices]

# Normalize
X = normalize(time_values, *time_range)
Z = normalize(time_after_values, *time_after_range)
Y = np.zeros_like(X)  # Keep Y fixed (Speed axis is ignored)

# Plot the line
ax.plot(X, Y, Z, color='red', linewidth=2, label="time + time_after = 45")
ax.legend()




speed_values = np.linspace(speed_range[0], speed_range[1], 10)  # Extend across full speed range
T, S = np.meshgrid(time_values, speed_values)
TA = 45 - T  # Apply the constraint

# Normalize for visualization
X = normalize(T, *time_range)
Y = normalize(S, *speed_range)
Z = normalize(TA, *time_after_range)

# Plot the plane
ax.plot_surface(X, Y, Z, color='red', alpha=0.3, edgecolor='none')



plt.show()




