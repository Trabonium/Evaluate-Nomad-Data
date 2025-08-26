import matplotlib as mpl

def set_plot_style(use_latex: bool = False):
    """
    Setzt globale Plot-Parameter für alle Plots.
    :param use_latex: True → LaTeX verwenden, False → Mathtext/Computer Modern
    """
    if use_latex:
        mpl.rcParams.update({
            "text.usetex": True,
            "font.family": "serif",
            "font.serif": ["Computer Modern"],
            "axes.labelsize": 13,
            "axes.titlesize": 14,
            "xtick.labelsize": 12,
            "ytick.labelsize": 12,
            "legend.fontsize": 12,
            "lines.linewidth": 1.5,
            "figure.dpi": 800,
        })
    else:
        mpl.rcParams.update({
            "text.usetex": False,
            "mathtext.fontset": "cm",
            "font.family": "serif",
            "font.serif": ["Times New Roman"],
            "axes.labelsize": 13,
            "axes.titlesize": 14,
            "xtick.labelsize": 12,
            "ytick.labelsize": 12,
            "legend.fontsize": 12,
            "lines.linewidth": 1.5,
            "figure.dpi": 800,
        })
# Standardmäßig ohne LaTeX