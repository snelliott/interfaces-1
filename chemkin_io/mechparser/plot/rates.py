"""
Plot the rates from a CHEMKIN mechanism file
"""
import os
import subprocess
import numpy as np
import matplotlib.pyplot as plt

# import the rate dictionary for now
from ktp import KTP_DCT
# Set the temps and pressuresfor now
TEMPS = np.array([500.0, 1000.0, 1500.0])

# Set plotting options
COLORS = ['k', 'b', 'r', 'g', 'm', 'y']
LINESTYLES = ['-', '--', '-.']
MARKERS = ['.', 'o', 's']

# Set various labels for plotting
FIG_TITLE = 'Comparison of Rate Data'
AXES_DCTS = [
    {'title': 'All rate constants'},
    {'title': 'Ratio of rate constants'}
]


def plot_rate_constants(ktp_dct, temps):
    """ run over the dictionary for plotting
    """

    # Initialize file string to species and file names 
    name_str = '{0:40s}{1}\n'.format('Name', 'Filename')

    # Plot the rate constants for each reaction
    reactions = list(KTP_DCT.keys())
    for i in range(0, len(reactions), 2):

        # Determine if plot will have two reactions in it, or one reaction
        if i+1 <= len(reactions)-1:
            nreactions = 2
        else:
            nreactions = 1

        # Create the figure object
        fig, axes = _build_figure(nreactions)

        # Set the axes object containing the plotted data for each reaction
        reactions_lst = []
        for j in range(nreactions):
            # Determine the reaction dictionaries
            reaction = reactions[i+j]
            reaction_mech_ktp_dcts = [KTP_DCT[reaction]['m1'], KTP_DCT[reaction]['m2']]
            reactions_lst.append(reaction)
            # Set variables needed for the plotting
            isbimol = _is_bimolecular(reaction)
            # Build the axes objects containing the plotted rate constants
            axes_col = axes[:,j] if nreactions == 2 else axes
            _build_axes(axes_col, reaction_mech_ktp_dcts, nreactions, isbimol, temps)
            
        # Update figure title with the reaction(s) on the page
        _set_figure_title(fig, reactions_lst)

        # Set the name of the plot
        name = 'r{0}'.format(str(i+1))
        name_str += '{0:40s}{1}\n'.format('reaction', name)
        
        # build and save the figure to a PDF
        fig.savefig('plots/{0}.pdf'.format(name), dpi=100)
        plt.close(fig)

    # Write file relating plot.pdf names to reaction names
    with open('names.txt', 'w') as name_file:
        name_file.write(name_str)

    # Collate all of the pdfs together
    _collate_pdfs()


def _build_figure(nreactions):
    """ Initialize the figure object
    """

    # Initialize plot objects
    if nreactions == 2:
        fig, axes = plt.subplots(nrows=2, ncols=2, figsize=(12, 8))    
    else:
        grid = {'width_ratios': [0.5]}
        fig, axes = plt.subplots(nrows=2, ncols=1, figsize=(12, 8), gridspec_kw=grid)    

    # Set various plot options
    fig.tight_layout()
    fig.subplots_adjust(left=0.075, 
                        top=0.925, bottom=0.075,
                        wspace=0.2, hspace=0.175)

    return fig, axes


def _build_axes(axes_col, reaction_mech_dcts, nreactions, isbimol, temps):
    """ plot the rates for various pressures
        certain checks are made throughout to deal with plotting 
        only one reaction on a page
    """
   
    # Obtain a list of the pressures and sort from low to high pressure
    reaction_pressures_lst = [_get_sorted_pressures(reaction)
                              for reaction in reaction_mech_dcts]
    reaction_pressures_union = _get_union_defined_pressures(reaction_pressures_lst)

    # Plot the data
    _full_plot(axes_col[0], reaction_mech_dcts, reaction_pressures_lst, temps)
    _ratio_plot(axes_col[1], reaction_mech_dcts, reaction_pressures_union, temps)
    axes_col[0].set(**_set_axes_labels(AXES_DCTS[0], isbimol, bottom=False))
    axes_col[1].set(**_set_axes_labels(AXES_DCTS[1], isbimol, bottom=True))


def _full_plot(ax_obj, mech_ktp_dcts, mech_pressures, temps):
    """ plot all the rate constants from two mechanisms
    """
    for i, ktp_dct in enumerate(mech_ktp_dcts):
        for j, pressure in enumerate(mech_pressures[i]):
            ax_obj.plot((1.0/temps), np.log(ktp_dct[pressure]),
                     color=COLORS[j], linestyle=LINESTYLES[i],
                     label='M'+str(i+1)+'-'+str(pressure))
    ax_obj.legend(loc='lower right')


def _ratio_plot(ax_obj, mech_ktp_dcts, pressures, temps):
    """ plot the ratio of rate constants from two mechanisms
    """
    [m1_ktp_dct, m2_ktp_dct] = mech_ktp_dcts
    for i, pressure in enumerate(pressures):
        m1_ktp = np.array(m1_ktp_dct[pressure])
        m2_ktp = np.array(m2_ktp_dct[pressure])
        ratios = (np.log(m1_ktp) / np.log(m2_ktp))
        ax_obj.plot((1.0/temps), ratios,
                    color=COLORS[i], linestyle=LINESTYLES[0],
                    label=pressure)
    ax_obj.legend(loc='lower right')


def _get_sorted_pressures(unsorted_pressures):
    """ get a sorted list of pressures for the reaction
    """
    pressures = [pressure for pressure in unsorted_pressures
                 if pressure != 'high']
    pressures.sort()
    pressures.append('high')
    return pressures


def _get_union_defined_pressures(pressures):
    """ get list of pressured where rates are defined for both mechanisms
    """
    [pr1, pr2] = pressures
    return list(set(pr1) & set(pr2)) 


def _is_bimolecular(reaction):
    """ Determines if a reaction is bimolecular
    """
    reactants = reaction[0]
    if len(reactants) == 2:
        isbimol = True
    else:
        isbimol = False
    return isbimol


def _set_axes_labels(axes_dct, isbimol, bottom):
    """ alter the axes dictionary
    """
    if isbimol:
        units = 'cm3/s'
    else:
        units = '1/s'

    if bottom:
        axes_dct['xlabel'] = '1/T (1/K)'
        axes_dct['ylabel'] = 'ln k1 / ln k2'
    else:
        axes_dct['ylabel'] = 'ln k({0})'.format(units)

    return axes_dct


def _set_figure_title(fig_obj, reactions_lst):
    """ Update the string for the figure title
    """
    reaction_str_lst = []
    for reaction in reactions_lst:
        side_strs = []
        for side in reaction:
            side_strs.append('+'.join(side))
        reaction_str_lst.append('->'.join(side_strs))

    if len(reactions_lst) == 2:
        fig_title = '{0:^80s}{1:^80s}'.format(reaction_str_lst[0], reaction_str_lst[1])
    else:
        fig_title = '{0:^80s}'.format(reaction_str_lst[0])

    fig_obj.suptitle(fig_title)


def _collate_pdfs():
    """ collate all of the pdfs together
    """
    plots = os.listdir('plots')
    plots.sort(key=lambda x: int(x.replace('r','').replace('.pdf','')))
    plots.append('all_rates.pdf')
    plots = [os.path.join('plots', name) for name in plots]

    command = ['pdfunite'] + plots
    subprocess.call(command)


if __name__ == '__main__':
    plot_rate_constants(KTP_DCT, TEMPS)
