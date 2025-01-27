import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkinter import simpledialog
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
        self.remove_button = tk.Button(self, text="Remove Last Process Step", command=self.remove_process)
        self.remove_button.pack(pady=10)

        # Button to generate the experiment plan (Excel file)
        self.generate_button = tk.Button(self, text="Generate Experiment Plan", command=self.generate_experiment_plan)
        self.generate_button.pack(pady=10)

        # List to hold the sequence of processes (this includes Experiment Info first)
        self.process_sequence = [{"process": "Experiment Info", "config": {}}]
        self.sequence_listbox.insert(tk.END, "Experiment Info")

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
            # Check if the selected process has additional parameters
            self.process_details = process_config.get(selected_process, {})

            if 'steps' in self.process_details:
                pass
            else:
                # No steps, add process details
                self.process_details = self.get_process_inputs_gui()

            # Add the selected process to the sequence
            self.process_sequence.append({"process": selected_process, "config": self.process_details})
            self.sequence_listbox.insert(tk.END, selected_process)

        else:
            messagebox.showwarning("Invalid Selection", "Please select a valid process.")

    def remove_process(self):
        if len(self.process_sequence) > 1:
            self.process_sequence.pop()
            self.sequence_listbox.delete(tk.END)
        else:
            messagebox.showwarning("Invalid Operation", "Cannot remove the Experiment Info step.")

    def generate_experiment_plan(self):
        if len(self.process_sequence) <= 1:
            messagebox.showwarning("Incomplete Sequence", "You must add processes before generating the plan.")
            return
        
        # Create an instance of ExperimentExcelBuilder with the updated sequence
        builder = ExperimentExcelBuilder(self.process_sequence, self.process_config)

        # Build and save the Excel file
        builder.build_excel()
        builder.save()

        messagebox.showinfo("Success", "Experiment plan has been generated and saved.")

        from tkinter import simpledialog

    def get_process_inputs_gui(self):
        """
        Dynamically get user inputs for all keys in the given dictionary via a GUI.
        :param process_details: Dictionary containing keys for expected inputs.
        :return: Dictionary with user-provided values for each key.
        """
        # Initialize tkinter
        root = tk.Tk()
        root.withdraw()  # Hide the main window

        # Iterate through keys and get input
        for key in self.process_details:
            while True:
                user_input = simpledialog.askstring("Input", f"Enter value for '{key}':")
                if user_input is None:  # User canceled
                    break
                try:
                    # Attempt to convert the input to match the data type
                    if isinstance(self.process_details[key], int):
                        self.process_details[key] = int(user_input)
                    elif isinstance(self.process_details[key], float):
                        self.process_details[key] = float(user_input)
                    else:
                        self.process_details[key] = user_input  # Default to string
                    break  # Break the loop if successful
                except ValueError:
                    tk.messagebox.showerror("Invalid Input", f"Invalid input for '{key}'. Please try again.")

        root.destroy()  # Close the tkinter app
        return self.process_details

# Main function to run the GUI application
def run_gui():
    app = ExperimentGUI()
    app.mainloop()

# Run the GUI application
if __name__ == "__main__":
    run_gui()
