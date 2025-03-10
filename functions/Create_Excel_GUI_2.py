import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from functions.Create_Excel_Script_1 import ExperimentExcelBuilder, process_config

def Excel_GUI(master):
    class ExperimentGUI(tk.Toplevel):
        def __init__(self, master):
            super().__init__(master)
            self.title("Experimental Plan Generator")
            self.geometry("400x400")

            # Sperrt die Interaktion mit dem Hauptfenster
            self.grab_set()

            # Label
            self.label = tk.Label(self, text="Select the steps for the experimental plan:")
            self.label.pack(pady=10)

            # Dropdown für Prozesse
            self.available_processes = self.get_process_names()
            self.process_combobox = ttk.Combobox(self, values=self.available_processes)
            self.process_combobox.pack(pady=10)

            # Hinzufügen-Button
            self.add_button = tk.Button(self, text="Add Process", command=self.add_process)
            self.add_button.pack(pady=10)

            # Listbox für ausgewählte Prozesse
            self.sequence_listbox = tk.Listbox(self, height=10, width=50)
            self.sequence_listbox.pack(pady=10)

            # Entfernen-Button
            self.remove_button = tk.Button(self, text="Remove Last Process Step", command=self.remove_process)
            self.remove_button.pack(pady=10)

            # Generieren-Button
            self.generate_button = tk.Button(self, text="Generate Experiment Plan", command=self.generate_experiment_plan)
            self.generate_button.pack(pady=10)

            # Liste mit Prozessschritten
            self.process_sequence = [{"process": "Experiment Info", "config": {}}]
            self.sequence_listbox.insert(tk.END, "Experiment Info")


        def get_process_names(self):
            """ Extracts the process names from process_config. """
            if isinstance(process_config, dict):
                return list(process_config.keys())
            elif isinstance(process_config, list):
                return process_config
            else:
                return []

        def add_process(self):
            """ Adds a selected process to the sequence. """
            selected_process = self.process_combobox.get()

            if selected_process and selected_process != "Experiment Info":
                process_details = process_config.get(selected_process, {})

                if 'steps' not in process_details:
                    process_details = self.get_process_inputs_gui(process_details)

                self.process_sequence.append({"process": selected_process, "config": process_details.copy()})
                self.sequence_listbox.insert(tk.END, selected_process)
            else:
                messagebox.showwarning("Invalid Selection", "Please select a valid process.")

        def remove_process(self):
            """ Removes the last added process from the sequence. """
            if len(self.process_sequence) > 1:
                self.process_sequence.pop()
                self.sequence_listbox.delete(tk.END)
            else:
                messagebox.showwarning("Invalid Operation", "Cannot remove the Experiment Info step.")

        def generate_experiment_plan(self):
            """ Generates and saves the experiment plan as an Excel file. """
            if len(self.process_sequence) <= 1:
                messagebox.showwarning("Incomplete Sequence", "You must add processes before generating the plan.")
                return

            builder = ExperimentExcelBuilder(self.process_sequence, process_config)
            builder.build_excel()
            builder.save()

            messagebox.showinfo("Success", "Experiment plan has been generated and saved.")

        def get_process_inputs_gui(self, process_details):
            """ Dynamically asks the user for process parameters via a GUI input dialog. """
            for key in process_details:
                while True:
                    user_input = simpledialog.askstring("Input", f"Enter value for '{key}':")
                    if user_input is None:
                        break
                    try:
                        if isinstance(process_details[key], int):
                            process_details[key] = int(user_input)
                        elif isinstance(process_details[key], float):
                            process_details[key] = float(user_input)
                        else:
                            process_details[key] = user_input
                        break
                    except ValueError:
                        tk.messagebox.showerror("Invalid Input", f"Invalid input for '{key}'. Please try again.")

            return process_details

        # Erzeuge das Fenster
    gui = ExperimentGUI(master)

    # Warte, bis das Fenster geschlossen wird
    master.wait_window(gui)

