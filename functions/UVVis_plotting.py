import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from scipy.interpolate import CubicSpline
from scipy.signal import argrelextrema, savgol_filter
from scipy.optimize import curve_fit

from functions.api_calls_get_data import get_specific_data_of_sample

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
        try:
            popt, _ = curve_fit(
                gaussian,
                x[fitting_range],
                y[fitting_range],
                p0=[y[peak], peak_energy, 0.05],
            )
            results.append((popt[1], popt, fitting_range))
        except RuntimeError:
            break

        y_masked[fitting_range] = 0
    return results


def UVVis_plotting(data, file_path, nomad_url, token):
    plt.rcParams.update({
        'font.size': 14,
        'axes.labelsize': 16,
        'xtick.labelsize': 14,
        'ytick.labelsize': 14,
        'legend.fontsize': 14,
    })

    fig, axs = plt.subplots(1, 2, figsize=(14, 7))

    # SORTIERUNG nach Variation:
    sort_index = np.argsort(data["variation"])
    # Neue Farbliste passend zur sortierten Reihenfolge:
    colors = plt.cm.viridis(np.linspace(0, 1, len(data)))

    # Durchsortierte Indizes laufen:
    for idx, i in enumerate(sort_index):
        try:
            # hole UV-Vis-Daten aus NOMAD
            uvvis_entries = get_specific_data_of_sample(
                sample_id=data["sample_id"][i],
                entry_type='peroTF_UVvisMeasurement',
                nomad_url=nomad_url,
                token=token
            )

            uvvis_data = uvvis_entries[0]

            # DataFrame bauen
            data_dict = {}
            for m in uvvis_data["measurements"]:
                name = m["name"]
                data_dict[name] = m["intensity"]
                if "wavelength" not in data_dict:
                    data_dict["wavelength"] = m["wavelength"]

            df = pd.DataFrame(data_dict)

            # photon energy berechnen
            df["photonenergy"] = 1239.841984 / df["wavelength"]

            # Spline, Ableitung, Smoothen
            energy_range = np.linspace(df["photonenergy"].min(), df["photonenergy"].max(), 1001)
            spline = CubicSpline(df["photonenergy"].tolist(), df["absorption"].tolist())
            interpolated_absorption = spline(energy_range)
            smoothed_absorption = savgol_filter(interpolated_absorption, window_length=101, polyorder=3)
            derivate_absorption = np.gradient(smoothed_absorption, energy_range)

            result = find_peaks_and_fit_gaussian(energy_range, derivate_absorption)

            # Plotten
            color = colors[idx]
            bandgap_list = []
            for bandgap_energy, popt, fitting_range in result:
                axs[1].plot(
                    energy_range[fitting_range],
                    gaussian(energy_range[fitting_range], *popt),
                    color=color,
                )
                axs[1].axvline(x=bandgap_energy, color=color, linestyle='--')
                bandgap_list.append(f"{bandgap_energy:.2f} eV")

            bandgap_list = bandgap_list[::-1]

            # Variations-Name als Label für Legende
            labelleft = data["variation"][i]

            # Variations-Name als Label für Legende
            labelright = "Band gap: "
            if bandgap_list:
                labelright += f"{', '.join(bandgap_list)}"
            else:
                labelright = " No band gap found"

            # Original-Absorption und Glättung plotten
            axs[0].plot(
                df["photonenergy"], df["absorption"],
                'o', alpha=0.5, color=color, label=labelleft
            )
            axs[0].plot(
                energy_range, smoothed_absorption,
                '-', color=color
            )

            # Derivate
            axs[1].plot(
                energy_range, derivate_absorption,
                '-', color=color, label=labelright
            )
        except Exception as e:
            print(f"Error processing sample {data['sample_id'][i]}: {e}")
            continue

    axs[0].set_xlabel('Photon Energy (eV)')
    axs[0].set_ylabel('Absorption (%)')
    axs[0].legend()

    axs[1].set_xlabel('Photon Energy (eV)')
    axs[1].set_ylabel('d(Absorption)/d(Energy)')
    axs[1].legend()

    plt.tight_layout()

    if file_path:
        plt.savefig(file_path, dpi=800)
    else:
        plt.show()

    return
