import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from scipy.interpolate import CubicSpline
from scipy.signal import argrelextrema, savgol_filter
from scipy.optimize import curve_fit
from scipy.stats import linregress

from functions.api_calls_get_data import get_specific_data_of_sample

def find_best_tauc_fit(x, y, min_range=0.15, max_range=0.35):
    best_fit = None
    best_r2 = -np.inf

    for start in range(len(x)):
        for end in range(start + 5, len(x)):
            x_fit = x[start:end]
            y_fit = y[start:end]

            if len(x_fit) < 10:
                continue

            energy_range = x_fit[-1] - x_fit[0]
            if energy_range < min_range or energy_range > max_range:
                continue

            slope, intercept, r_value, *_ = linregress(x_fit, y_fit)
            r_squared = r_value**2
            if slope < 0 or r_squared < 0.98:
                continue

            x0 = -intercept / slope
            if 0.5 < x0 < 3.5:
                if r_squared > best_r2:
                    best_r2 = r_squared
                    best_fit = {
                        "x_fit": x_fit,
                        "y_fit": y_fit,
                        "slope": slope,
                        "intercept": intercept,
                        "bandgap": x0,
                        "r2": r_squared
                    }

    return best_fit


def gaussian(x, amp, cen, wid):
        return amp * np.exp(-((x - cen) ** 2) / (2 * wid**2))

def find_peaks_and_fit_gaussian(x, y):
        peaks = argrelextrema(y, np.greater)[0]
        if peaks.size == 0:
            return []
        results = []
        y_masked = np.copy(y)
        while True:
            peaks = argrelextrema(y_masked, np.greater)[0]
            if peaks.size == 0:
                break
            peak = peaks[np.argmax(y_masked[peaks])]
            peak_energy = x[peak]
            if len(results) > 0 and y_masked[peak] < results[0][1][0] / 4:
                break
            fitting_range = (x > peak_energy - 0.1) & (x < peak_energy + 0.1)
            width = 0.05
            try:
                popt, _ = curve_fit(
                    gaussian,
                    x[fitting_range],
                    y[fitting_range],
                    p0=[y[peak], peak_energy, width],
                )
                results.append((popt[1], popt, fitting_range))
            except RuntimeError:
                break
            y_masked[fitting_range] = 0
        return results

def plot_tauc(data, file_path, nomad_url, token, Latex_UVVis):
    #alpha = 1/d * ln( (1-R)^2 / T )
    thickness_nm = 550  # Schichtdicke in nm

    from functions.plot_style import set_plot_style_UVVis
    set_plot_style_UVVis(Latex_UVVis)

    fig, ax = plt.subplots(figsize=(10, 7))

    sort_index = range(len(data["sample_id"]))
    colors = plt.cm.viridis(np.linspace(0, 1, len(data)))

    for idx, i in enumerate(sort_index):
        try:
            uvvis_entries = get_specific_data_of_sample(
                sample_id=data["sample_id"][i],
                entry_type='peroTF_UVvisMeasurement',
                nomad_url=nomad_url,
                token=token
            )

            uvvis_data = uvvis_entries[0]
            data_dict = {}
            for m in uvvis_data["measurements"]:
                name = m["name"]
                data_dict[name] = m["intensity"]
                if "wavelength" not in data_dict:
                    data_dict["wavelength"] = m["wavelength"]

            df = pd.DataFrame(data_dict)

            # Energie berechnen
            df["energy_ev"] = 1239.841984 / df["wavelength"]
            df.sort_values("energy_ev", inplace=True)

            df['alpha'] = 1 / thickness_nm * np.log((1-df["reflection"]) ** 2 / df["transmission"])
            df['tauc'] = (df['alpha'] * df['energy_ev']) ** 2

            # Glättung
            x = df['energy_ev'].values
            y = df['tauc'].values
            y_smooth = savgol_filter(y, 51, 3)
            
            '''
            # Erste Ableitung
            dy = np.diff(y_smooth)
            dx = np.diff(x)
            derivative = dy / dx

            max_index = np.argmax(savgol_filter(derivative, 101, 3))
            if max_index < 10 or max_index + 10 >= len(x):
                raise RuntimeError("Not enough data points for fitting.")

            x_fit = x[max_index - 10: max_index + 10]
            y_fit = y_smooth[max_index - 10: max_index + 10]

            #find stable Tauc fit
            fit_result = find_best_tauc_fit(x, y_smooth)
            if fit_result is None:
                print(f"Fit is too bad {data['sample_id'][i]}")
                continue

            x_fit = fit_result["x_fit"]
            y_fit = fit_result["y_fit"]
            slope = fit_result["slope"]
            intercept = fit_result["intercept"]
            bandgap = round(fit_result["bandgap"], 2)
            '''

            # Plotten
            color = colors[idx]
            #label = f"{data['variation'][i]} (Eg = {bandgap} eV)"

            ax.plot(x, y, '-', color=color, alpha=0.5, label = f"{data['variation'][i]}")
            #ax.plot(x_fit, y_fit, '-', color=color)
            #x_line = np.linspace(bandgap, x[max_index], 100)
            #y_line = slope * x_line + intercept
            #ax.plot(x_line, y_line, '--', color=color, linewidth=2, label=label)
            #ax.scatter([bandgap], [0], color=color, zorder=5)

        except Exception as e:
            print(f"Error with sample {data['sample_id'][i]}: {e}")
            continue

    ax.set_xlabel('Photon Energy (eV)')
    ax.set_ylabel('$(αhv)^2$ (a.u.)')
    ax.set_title('Tauc-Plot (direct semiconductor)')
    ax.grid(True)
    ax.legend()
    plt.tight_layout()

    if file_path:
        plt.savefig(file_path, dpi=800)
    else:
        plt.show()


def plot_uvvis_photon_energy(data, file_path, nomad_url, token, Latex_UVVis):
    # === Plot-Setup ===
    from functions.plot_style import set_plot_style_UVVis
    set_plot_style_UVVis(Latex_UVVis)

    fig, axs = plt.subplots(1, 2, figsize=(14, 7))

    sort_index = range(len(data["sample_id"]))
    colors = plt.cm.viridis(np.linspace(0, 1, len(data)))

    for idx, i in enumerate(sort_index):
        try:
            uvvis_entries = get_specific_data_of_sample(
                sample_id=data["sample_id"][i],
                entry_type='peroTF_UVvisMeasurement',
                nomad_url=nomad_url,
                token=token
            )

            uvvis_data = uvvis_entries[0]
            data_dict = {}
            for m in uvvis_data["measurements"]:
                name = m["name"]
                data_dict[name] = m["intensity"]
                if "wavelength" not in data_dict:
                    data_dict["wavelength"] = m["wavelength"]

            df = pd.DataFrame(data_dict)

            # Energie berechnen
            df["photonenergy"] = 1239.841984 / df["wavelength"]

            # Interpolation und Ableitung in Energie
            energy_range = np.linspace(df["photonenergy"].min(), df["photonenergy"].max(), 1001)
            spline = CubicSpline(df["photonenergy"], df["absorption"])
            interpolated_absorption = spline(energy_range)
            smoothed_absorption = savgol_filter(interpolated_absorption, window_length=101, polyorder=3)
            derivate_absorption = np.gradient(smoothed_absorption, energy_range)

            # Bandlücken finden
            result = find_peaks_and_fit_gaussian(energy_range, derivate_absorption)

            # Farbwahl & Labels
            color = colors[idx]
            labelleft = data["variation"][i]
            bandgap_list = []
            for bandgap_energy, _, _ in result:
                bandgap_list.append(f"{bandgap_energy:.2f} eV")
            bandgap_list = bandgap_list[::-1]
            labelright = "Band gap: " + (", ".join(bandgap_list) if bandgap_list else "No band gap found")

            # === Plot in photon_energy ===
            
            axs[0].plot(df["photonenergy"], df["absorption"], 'o', alpha=0.5, color=color, label=labelleft)
            axs[0].plot(energy_range, smoothed_absorption, '-', color=color)
            axs[1].plot(energy_range, derivate_absorption, '-', color=color, label=labelright)

            for bandgap_energy, popt, fitting_range in result:
                axs[1].plot(
                    energy_range[fitting_range],
                    gaussian(energy_range[fitting_range], *popt),
                    color=color,
                )
                axs[1].axvline(x=bandgap_energy, color=color, linestyle='--')

            axs[0].set_xlabel("Photon Energy (eV)")
            axs[1].set_xlabel("Photon Energy (eV)")
            axs[1].set_ylabel("d(Absorption)/d(Energy)")

            if Latex_UVVis:
                axs[0].set_ylabel(r"Absorption (\%)")
            else:
                axs[0].set_ylabel("Absorption (%)")

        except Exception as e:
            print(f"Error processing sample {data['sample_id'][i]}: {e}")
            continue

    axs[0].legend()
    axs[1].legend()
    plt.tight_layout()

    if file_path:
        plt.savefig(file_path, dpi=800)
    else:
        plt.show()

    return

def plot_uvvis_wavelength(data, file_path, nomad_url, token, Latex_UVVis):
    # === Plot-Setup ===
    from functions.plot_style import set_plot_style_UVVis
    set_plot_style_UVVis(Latex_UVVis)

    fig, axs = plt.subplots(1, 2, figsize=(14, 7))

    sort_index = range(len(data["sample_id"]))
    colors = plt.cm.viridis(np.linspace(0, 1, len(data)))

    for idx, i in enumerate(sort_index):
        try:
            uvvis_entries = get_specific_data_of_sample(
                sample_id=data["sample_id"][i],
                entry_type='peroTF_UVvisMeasurement',
                nomad_url=nomad_url,
                token=token
            )

            uvvis_data = uvvis_entries[0]
            data_dict = {}
            for m in uvvis_data["measurements"]:
                name = m["name"]
                data_dict[name] = m["intensity"]
                if "wavelength" not in data_dict:
                    data_dict["wavelength"] = m["wavelength"]

            df = pd.DataFrame(data_dict)

            # Energie berechnen
            df["photonenergy"] = 1239.841984 / df["wavelength"]

            # Interpolation und Ableitung in Energie
            energy_range = np.linspace(df["photonenergy"].min(), df["photonenergy"].max(), 1001)
            spline = CubicSpline(df["photonenergy"], df["absorption"])
            interpolated_absorption = spline(energy_range)
            smoothed_absorption = savgol_filter(interpolated_absorption, window_length=101, polyorder=3)
            derivate_absorption = np.gradient(smoothed_absorption, energy_range)

            # Bandlücken finden
            result = find_peaks_and_fit_gaussian(energy_range, derivate_absorption)

            # Farbwahl & Labels
            color = colors[idx]
            labelleft = data["variation"][i]
            bandgap_list = []
            for bandgap_energy, _, _ in result:
                bandgap_list.append(f"{bandgap_energy:.2f} eV")
            bandgap_list = bandgap_list[::-1]
            labelright = "Band gap: " + (", ".join(bandgap_list) if bandgap_list else "No band gap found")

            # === Plot in wavelength ===
            # x-Werte konvertieren
            wavelength_range = 1239.841984 / energy_range[::-1]
            smoothed_absorption = smoothed_absorption[::-1]
            derivate_absorption = derivate_absorption[::-1]

            axs[0].plot(df["wavelength"], df["absorption"], 'o', alpha=0.5, color=color, label=labelleft)
            axs[0].plot(wavelength_range, smoothed_absorption, '-', color=color)
            axs[1].plot(wavelength_range, derivate_absorption, '-', color=color, label=labelright)

            for bandgap_energy, popt, fitting_range in result:
                lambda_fit = 1239.841984 / energy_range[fitting_range][::-1]
                axs[1].plot(
                    lambda_fit,
                    gaussian(energy_range[fitting_range], *popt)[::-1],
                    color=color,
                )
                lambda_bg = 1239.841984 / bandgap_energy
                axs[1].axvline(x=lambda_bg, color=color, linestyle='--')

            axs[0].set_xlabel("Wavelength (nm)")
            axs[1].set_xlabel("Wavelength (nm)")
            axs[0].invert_xaxis()  # ⬅️ neu: linke Achse invertieren!
            axs[1].invert_xaxis()
            axs[1].set_ylabel("d(Absorption)/d(Wavelength)")
            if Latex_UVVis:
                axs[0].set_ylabel(r"Absorption (\%)")
            else:
                axs[0].set_ylabel("Absorption (%)")

        except Exception as e:
            print(f"Error processing sample {data['sample_id'][i]}: {e}")
            continue

    axs[0].legend()
    axs[1].legend()
    plt.tight_layout()

    if file_path:
        plt.savefig(file_path, dpi=800)
    else:
        plt.show()

    return

def UVVis_plotting(data, file_path, Latex_UVVis, nomad_url, token, unit):
    if unit == "tauc_plot":
        return plot_tauc(data, file_path, nomad_url, token, Latex_UVVis)
    elif unit == "photon_energy":
        return plot_uvvis_photon_energy(data, file_path, nomad_url, token, Latex_UVVis)
    elif unit == "wavelength":
        return plot_uvvis_wavelength(data, file_path, nomad_url, token, Latex_UVVis)
    else:
        raise ValueError(f"Unknown unit: {unit}")