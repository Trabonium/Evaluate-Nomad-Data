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


def UVVis_plotting(data, file_path, nomad_url, token, unit):
    import matplotlib.pyplot as plt
    import pandas as pd
    import numpy as np
    from scipy.interpolate import CubicSpline
    from scipy.signal import argrelextrema, savgol_filter
    from scipy.optimize import curve_fit

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

    # === Plot-Setup ===
    plt.rcParams.update({
        'font.size': 14,
        'axes.labelsize': 16,
        'xtick.labelsize': 14,
        'ytick.labelsize': 14,
        'legend.fontsize': 14,
    })

    fig, axs = plt.subplots(1, 2, figsize=(14, 7))

    sort_index = np.argsort(data["variation"])
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
            if unit == "photon_energy":
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

            # === Plot in wavelength ===
            # === Plot in wavelength ===
            else:
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
