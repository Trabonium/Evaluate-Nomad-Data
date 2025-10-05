import math
import tkinter as tk
from tkinter import filedialog, messagebox
from scipy.stats.qmc import LatinHypercube
from sympy import isprime

def get_latin_hypercube_sample(dimensionality: int, n_samples: int, scramble: bool= False, enhanced_orthoganal_sampling: bool = True) -> list:
    orthogonal_strength = 2 if enhanced_orthoganal_sampling else 1
    LHC = LatinHypercube(d=dimensionality, scramble=scramble, strength=orthogonal_strength)
    
    #check if a valid sample count is given if a strength 2 orthogonal LHC is selected
    if enhanced_orthoganal_sampling:
        is_samplecount_square = math.sqrt(n_samples) == round(math.sqrt(n_samples), 0)
        is_samplecounts_sqrt_prime = isprime(int(math.sqrt(n_samples)))
        if not(is_samplecount_square and is_samplecounts_sqrt_prime):
            raise ValueError("for strength 2 orthogonal sampling, sample count must be a prime squared")
    
    return LHC.random(n_samples)

def _denormalize_samples(samples: list, normalization_bounds: list)->list:
    denorm_samples = samples.copy()
    for dim in range(len(normalization_bounds)):
        for s in denorm_samples:
            s[dim] = (s[dim] * (normalization_bounds[dim][1] - normalization_bounds[dim][0])) + normalization_bounds[dim][0]
    
    return denorm_samples

def roundPartial (value:float, resolution:float)->float:
    return round(round (value / resolution) * resolution, 10)


def latin_hypercube_sampling_gui(master):
 
    def start_generation():
        dimensionality = len(rows)

        try:
            samples = get_latin_hypercube_sample(dimensionality=dimensionality, n_samples=var_sample_count.get(), scramble=scrambling.get(), enhanced_orthoganal_sampling=orthogonal_sampling.get())
        except ValueError as error:
            show_error(str(error))
            return
        
        bounds = []
        for row in rows:
            bounds.append([row[1].get(), row[2].get()])

        stepsize = [r[3].get() for r in rows]


        for b in bounds:
            if b[0] >= b[1]:
                show_error("Please specify upper bounds that are greater than lower bounds")
                return
        for f in stepsize:
            if(f<=0):
                show_error("step size must be greater than 0")
                return

        samples = _denormalize_samples(samples=samples, normalization_bounds=bounds)
        #round to step size
        for s in samples:
            for a in range(dimensionality):
                s[a] = roundPartial(s[a],stepsize[a])

        output_box.grid() #show output box
        firstline = str(rows[0][0].get())
        for n in range(len(rows)-1):
            firstline += ";"
            firstline += rows[n+1][0].get()
        output_box.delete("1.0", "end")
        output_box.insert("end", firstline + "\n")

        for s in samples:
            sample_string = str(s[0])
            for d in range(dimensionality-1):
                sample_string += ";"
                sample_string += str(s[d+1])
            output_box.insert("end", sample_string + "\n")


    def add_row():
        row_index = len(rows)+1
        name_var = tk.StringVar()
        low_var = tk.DoubleVar()
        high_var = tk.DoubleVar()
        stepsize_var = tk.DoubleVar()

        # Create entries
        name_entry = tk.Entry(form_frame, textvariable=name_var, width=30)
        low_entry = tk.Entry(form_frame, textvariable=low_var, width=15)
        high_entry = tk.Entry(form_frame, textvariable=high_var, width=15)
        step_entry = tk.Entry(form_frame, textvariable=stepsize_var, width=15)

        # Place them in a grid
        name_entry.grid(row=row_index, column=0, padx=5, pady=2)
        low_entry.grid(row=row_index, column=1, padx=5, pady=2)
        high_entry.grid(row=row_index, column=2, padx=5, pady=2)
        step_entry.grid(row=row_index, column=3, padx=5, pady=2)

        rows.append((name_var, low_var, high_var, stepsize_var))

    def hide_error():
        errortext.config(text="")
        errortext.grid_remove()
        errorclose.grid_remove()

    def show_error(errormsg: str):
        errortext.config(text=errormsg)
        errortext.grid()
        errorclose.grid()
        

    lhs_gui_window = tk.Toplevel(master)
    lhs_gui_window.title("Latin Hypercube Sample Generator")
    
    # Container for rows
    form_frame = tk.Frame(lhs_gui_window)
    form_frame.grid(row=1, columnspan=5, padx=10, pady=10)

    tk.Label(form_frame, text="Variable Name").grid(row=0, column=0, padx=5, pady=10)
    tk.Label(form_frame, text="Lower Bound").grid(row=0, column=1, padx=5, pady=10)
    tk.Label(form_frame, text="Upper Bound").grid(row=0, column=2, padx=5, pady=10)
    tk.Label(form_frame, text="Step size").grid(row=0, column=3, padx=5, pady=10)

    rows = []
    add_row()

    add_button = tk.Button(lhs_gui_window, text="➕ Add Row", command=add_row)
    add_button.grid(row=2, column=0, pady=10)

    var_sample_count = tk.IntVar()
    tk.Label(lhs_gui_window, text="Sample count:").grid(row=3, column=0, padx=10, pady=10)
    sample_count_entry = tk.Entry(lhs_gui_window, textvariable=var_sample_count, width=30)
    sample_count_entry.grid(row=3, column=1, padx=10, pady=10)

    scrambling = tk.BooleanVar()
    toggle_button = tk.Checkbutton(lhs_gui_window, text="Scramble samples", variable=scrambling)
    toggle_button.grid(row=4, column=0, padx=10, pady=10)

    orthogonal_sampling = tk.BooleanVar(value=True)
    toggle_button = tk.Checkbutton(lhs_gui_window, text="Enhanced distribution", variable=orthogonal_sampling)
    toggle_button.grid(row=4, column=1, padx=10, pady=10)

    tk.Button(lhs_gui_window, text="Generate", command=start_generation).grid(row=5, columnspan=3, pady=20)

    output_box = tk.Text(lhs_gui_window, height=8, width=60, wrap="word", state="normal")
    output_box.grid(row=6, column=0, padx=10, pady=10)
    output_box.grid_remove()

    errortext = tk.Label(lhs_gui_window, text="", fg='#f00')
    errortext.grid(row=7, column=0, padx=10, pady=10)
    errortext.grid_remove()

    errorclose = tk.Button(lhs_gui_window, text="❌", fg='#f00', command=hide_error)
    errorclose.grid(row=7, column=1, padx=10, pady=0)
    errorclose.grid_remove()

    lhs_gui_window.grab_set()
    lhs_gui_window.wait_window()
    return
