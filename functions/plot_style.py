import matplotlib as mpl

def set_plot_style(use_latex: bool = False):
    if use_latex:
        mpl.rcParams.update({
            "text.usetex": True,
            "font.family": "serif",
            "font.serif": ["Computer Modern"],
            "axes.labelsize": 14,   # was 13
            "axes.titlesize": 16,   # was 14
            "xtick.labelsize": 13,  # was 12
            "ytick.labelsize": 13,
            "legend.fontsize": 13,
            "lines.linewidth": 1.5,
            "figure.dpi": 600,  # 600 is sufficient for print
        })
    else:
        mpl.rcParams.update({
            "text.usetex": False,
            "mathtext.fontset": "cm",
            "font.family": "serif",
            "font.serif": ["Times New Roman"],  # matches many thesis guidelines
            "axes.labelsize": 14,
            "axes.titlesize": 16,
            "xtick.labelsize": 13,
            "ytick.labelsize": 13,
            "legend.fontsize": 13,
            "lines.linewidth": 1.5,
            "figure.dpi": 600,
        })


def set_plot_style_UVVis(use_latex: bool = False):
    """
    Global plot parameters
    :param use_latex: True → Use LaTeX, False → Use Mathtext/Computer Modern
    """
    if use_latex:
        mpl.rcParams.update({
            "text.usetex": True,
            "font.family": "serif",
            "font.serif": ["Computer Modern"],
            "axes.labelsize": 16,
            "axes.titlesize": 16,
            "xtick.labelsize": 18,
            "ytick.labelsize": 18,
            "legend.fontsize": 14,
            "lines.linewidth": 1.5,
            "figure.dpi": 800,
        })
    else:
        mpl.rcParams.update({
            "text.usetex": False,
            "mathtext.fontset": "cm",
            "font.family": "serif",
            "font.serif": ["Times New Roman"],
            "axes.labelsize": 16,
            "axes.titlesize": 16,
            "xtick.labelsize": 18,
            "ytick.labelsize": 18,
            "legend.fontsize": 14,
            "lines.linewidth": 1.5,
            "figure.dpi": 800,
        })

def set_ppt_style(use_latex: bool = True):
    if use_latex:
        mpl.rcParams.update({
            "text.usetex": True,
            "font.family": "sans-serif",
            "font.sans-serif": ["Helvetica"],  # or "Arial"
            "axes.labelsize": 22,
            "axes.titlesize": 24,
            "xtick.labelsize": 20,
            "ytick.labelsize": 20,
            "legend.fontsize": 20,
            "lines.linewidth": 2,
            "figure.dpi": 300,   # high enough for slides
        })
    else:
        mpl.rcParams.update({
            "text.usetex": False,
            "mathtext.fontset": "stixsans",  # clean sans-serif math style
            "font.family": "sans-serif",
            "font.sans-serif": ["Helvetica"],  # or "Arial"
            "axes.labelsize": 22,
            "axes.titlesize": 24,
            "xtick.labelsize": 20,
            "ytick.labelsize": 20,
            "legend.fontsize": 20,
            "lines.linewidth": 2,
            "figure.dpi": 300,
        })

        