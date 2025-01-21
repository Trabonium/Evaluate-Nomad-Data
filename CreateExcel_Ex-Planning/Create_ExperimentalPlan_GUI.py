import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from create_excel import ExperimentExcelBuilder, process_config

class ExperimentGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Experimental Plan Generator")
        self.geometry("400x400")

        # Label to prompt the user
        self.label = tk.Label(self, text="Select the steps for the experimental plan:")
        self.label.pack(pady=10)

        # Dynamically extract process names from process_config
        self.available_processes = self.get_process_names()

        # Dropdown for selecting processes
        self.process_combobox = ttk.Combobox(self, values=self.available_processes)
        self.process_combobox.pack(pady=10)

        # Button to add selected process to sequence
        self.add_button = tk.Button(self, text="Add Process", command=self.add_process)
        self.add_button.pack(pady=10)

        # Listbox to show the selected sequence of processes
        self.sequence_listbox = tk.Listbox(self, height=10, width=50)
        self.sequence_listbox.pack(pady=10)

        # Button to generate the experiment plan (Excel file)
        self.generate_button = tk.Button(self, text="Generate Experiment Plan", command=self.generate_experiment_plan)
        self.generate_button.pack(pady=10)

        # List to hold the sequence of processes (this includes Experiment Info first)
        self.process_sequence = [{"process": "Experiment Info", "config": {}}]

        # To hold the current process's additional parameters
        self.current_process_params = None

    def get_process_names(self):
        """
        Extracts the process names from the imported process_config.
        """
        if isinstance(process_config, dict):
            return list(process_config.keys())
        elif isinstance(process_config, list):
            return process_config
        else:
            return []

    def add_process(self):
        # Get selected process from combobox
        selected_process = self.process_combobox.get()

        if selected_process and selected_process != "Experiment Info":
            # Add the experiment info first if not already present
            if not any(step["process"] == "Experiment Info" for step in self.process_sequence):
                self.process_sequence.insert(0, {"process": "Experiment Info", "config": {}})
                self.sequence_listbox.insert(tk.END, "Experiment Info")

            # Check if the selected process has additional parameters
            process_details = process_config.get(selected_process, {})

            # Add the selected process to the sequence
            self.process_sequence.append({"process": selected_process, "config": {}})
            self.sequence_listbox.insert(tk.END, selected_process)

            # If the selected process has extra parameters, ask the user to input them
            if "steps" in process_details:
                self.ask_for_additional_parameters(selected_process, process_details)

        else:
            messagebox.showwarning("Invalid Selection", "Please select a valid process.")

    def ask_for_additional_parameters(self, process_name, process_details):
        """
        Prompt the user to enter additional parameters such as solvents, solutes, or materials.
        This will only prompt if the selected process has additional data.
        """
        # Create a new window for parameter input
        param_window = tk.Toplevel(self)
        param_window.title(f"Input Parameters for {process_name}")
        param_window.geometry("300x200")

        # Label for the process
        label = tk.Label(param_window, text=f"Enter parameters for {process_name}:")
        label.pack(pady=10)

        # Loop through the additional parameters in the process
        for param, value in process_details.items():
            if param != "steps":  # Skip the steps key
                # Create a label and an entry for each parameter
                param_label = tk.Label(param_window, text=f"{param}:")
                param_label.pack(pady=5)
                param_entry = tk.Entry(param_window)
                param_entry.pack(pady=5)
                param_entry.insert(0, str(value))  # Default value as the current one

                # Store the entry widget for later retrieval
                if not hasattr(self, 'entries'):
                    self.entries = {}

                self.entries[param] = param_entry

        # Button to confirm and close the parameter input window
        confirm_button = tk.Button(param_window, text="Confirm", command=lambda: self.confirm_parameters(param_window))
        confirm_button.pack(pady=10)

    def confirm_parameters(self, param_window):
        """
        Confirm the parameters entered by the user and close the parameter window.
        """
        # Retrieve values from the input fields and store them in the sequence
        for param, entry in self.entries.items():
            value = entry.get()
            # Validate the integer input (if the value is an integer)
            if param != "steps":
                try:
                    value = int(value)
                    # Append the parameter to the process configuration
                    self.process_sequence[-1]["config"][param] = value
                except ValueError:
                    messagebox.showerror("Invalid Input", f"Please enter a valid integer for {param}.")
                    return

        param_window.destroy()

    def generate_experiment_plan(self):
        if len(self.process_sequence) <= 1:
            messagebox.showwarning("Incomplete Sequence", "You must add processes before generating the plan.")
            return
        
        # Create an instance of ExperimentExcelBuilder with the updated sequence
        builder = ExperimentExcelBuilder(self.process_sequence, process_config)

        # Build and save the Excel file
        builder.build_excel()
        builder.save()

        messagebox.showinfo("Success", "Experiment plan has been generated and saved.")

# Main function to run the GUI application
def run_gui():
    app = ExperimentGUI()
    app.mainloop()

# Run the GUI application
if __name__ == "__main__":
    run_gui()
