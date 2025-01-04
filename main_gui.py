import tkinter as tk
from tkinter import filedialog, messagebox
import requests
import pandas as pd

from functions.get_data import get_data_excel_to_df
from functions.calculate_statistics import calculate_statistics
from functions.plotting_functions import plot_box_and_scatter, plot_JV_curves, plot_EQE_curves, plot_MPP_curves
from functions.generate_report import generate_pdf_report

# Initialize variables
selected_file_path = None
data = None
stats = None
token = None

# Global variables for URL and token
nomad_url = "http://elnserver.lti.kit.edu/nomad-oasis/api/v1"
token = None  # This will store the token


# Function to log in to NOMAD
def login_handler():
    global token, nomad_url
    username = username_entry.get()
    password = password_entry.get()

    if not username or not password:
        messagebox.showerror("Error", "Please enter both username and password.")
        return

    try:
        # Get a token from the NOMAD API
        response = requests.get(
            f"{nomad_url}/auth/token", params=dict(username=username, password=password)
        )
        response.raise_for_status()  # Raise an error if the request failed
        token = response.json()['access_token']

        # Test the token by fetching uploads
        uploads_response = requests.get(
            f"{nomad_url}/uploads",
            headers={"Authorization": f"Bearer {token}"}
        )
        uploads_response.raise_for_status()

        # Success message
        messagebox.showinfo("Login Success", f"Logged in as {username}")
    except requests.exceptions.RequestException as e:
        messagebox.showerror("Login Failed", f"Error: {e}")


# Function to select an Excel file
def select_file():
    global selected_file_path
    selected_file_path = filedialog.askopenfilename(title="Select Excel File", filetypes=[("Excel files", "*.xlsx")])
    if selected_file_path:
        file_path_label.config(text=f"Selected File: {selected_file_path}")


# Function to load data from the selected file
def load_data():
    global data
    if not selected_file_path:
        messagebox.showerror("Error", "Please select an Excel file first.")
        return
    try:
        data = get_data_excel_to_df(selected_file_path, nomad_url, token)
        messagebox.showinfo("Success", "Data loaded successfully!")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to load data: {e}")


# Function to calculate statistics
def calculate_stats():
    global data, stats
    if data is None:
        messagebox.showerror("Error", "Load data first!")
        return
    try:
        stats = calculate_statistics(data)
        messagebox.showinfo("Success", "Statistics calculated successfully!")
        print(stats)
    except Exception as e:
        messagebox.showerror("Error", f"Failed to calculate statistics: {e}")


# Function to generate PDF report
def generate_report():
    global data, stats

    if data is None or stats is None:
        messagebox.showerror("Error", "Please load data and calculate statistics first.")
        return

    # Get file name and path
    file_path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF files", "*.pdf")])
    if not file_path:
        return

    # Get selected plot options
    selected_plots = {
        "JV": jv_var.get(),
        "Box+Scatter": box_var.get(),
        "EQE": eqe_var.get(),
        "MPP": mpp_var.get(),
        "Table": table_var.get(),
    }

    try:
        # Generate the PDF report
        generate_pdf_report(data, stats, selected_plots, file_path, nomad_url, token)
        messagebox.showinfo("Success", f"PDF report saved to: {file_path}")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to generate report: {e}")


# Create main application window
root = tk.Tk()
root.title("Data Analysis GUI")
root.geometry("600x600")

# Login Section
tk.Label(root, text="NOMAD Login", font=("Helvetica", 12, "bold")).pack(pady=5)

username_label = tk.Label(root, text="Username:")
username_label.pack()
username_entry = tk.Entry(root, width=30)
username_entry.pack()

password_label = tk.Label(root, text="Password:")
password_label.pack()
password_entry = tk.Entry(root, width=30, show="*")
password_entry.pack()

login_button = tk.Button(root, text="Login", command=login_handler)
login_button.pack(pady=10)

# File Selection Section
tk.Label(root, text="Excel File Selection", font=("Helvetica", 12, "bold")).pack(pady=10)
file_select_button = tk.Button(root, text="Select File", command=select_file)
file_select_button.pack()
file_path_label = tk.Label(root, text="No file selected", fg="gray")
file_path_label.pack()

# Data and Statistics Buttons
tk.Button(root, text="Load corresponding Data from NOMAD OASIS", command=load_data).pack(pady=10)
tk.Button(root, text="Calculate Statistics", command=calculate_stats).pack(pady=10)

# Plot Selection Section
tk.Label(root, text="Select Plots for Report", font=("Helvetica", 12, "bold")).pack(pady=10)

jv_var = tk.BooleanVar(value=True)
box_var = tk.BooleanVar(value=True)
eqe_var = tk.BooleanVar(value=False)
mpp_var = tk.BooleanVar(value=False)
table_var = tk.BooleanVar(value=True)

tk.Checkbutton(root, text="JV Curves", variable=jv_var).pack()
tk.Checkbutton(root, text="Box + Scatter Plots", variable=box_var).pack()
tk.Checkbutton(root, text="EQE Curves", variable=eqe_var).pack()
tk.Checkbutton(root, text="MPP Curves", variable=mpp_var).pack()
tk.Checkbutton(root, text="Data Table", variable=table_var).pack()

# Report Generation Button
tk.Button(root, text="Generate Report", command=generate_report).pack(pady=20)

# Run the application
root.mainloop()
