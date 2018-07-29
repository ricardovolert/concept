# This file is part of CO𝘕CEPT, the cosmological 𝘕-body code in Python.
# Copyright © 2015–2018 Jeppe Mosgaard Dakin.
#
# CO𝘕CEPT is free software: You can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# CO𝘕CEPT is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with CO𝘕CEPT. If not, see http://www.gnu.org/licenses/
#
# The author of CO𝘕CEPT can be contacted at dakin(at)phys.au.dk
# The latest version of CO𝘕CEPT is available at
# https://github.com/jmd-dk/concept/



# Imports from the CO𝘕CEPT code
from commons import *
from integration import cosmic_time, initiate_time

# Absolute path and name of the directory of this file
this_dir  = os.path.dirname(os.path.realpath(__file__))
this_test = os.path.basename(this_dir)

# As this non-compiled code should work regardless of whether
# the main CO𝘕CEPT code is compiled or not, we need to flood
# this name space with names from commons explicitly, as
# 'from commons import *' does not import C level variables.
commons_flood()

# Initiate the cosmic time and the scale factor,
# and do the call to CLASS if enable_class_background is True.
initiate_time()

# Array of scale factor values at which to compute the cosmic time
N_points = 50
scale_factors = logspace(log10(a_begin), log10(1), N_points)

# Compute the cosmic time for each value of the scale factor
cosmic_times = [cosmic_time(a) for a in scale_factors]

# Dependent on the mode, save the computed cosmic times
compiled = not user_params['_pure_python']
mode = f'class={enable_class_background}_compiled={compiled}'
np.savetxt(f'{this_dir}/t_{mode}.dat', cosmic_times)

# If all four data files exist, plot and analyze these
data_filenames = glob(f'{this_dir}/*.dat')
if sum([bool(re.search(f'^{this_dir}/t_class=(True|False)_compiled=(True|False)\.dat$' , fname))
       for fname in data_filenames]) == 4:
    masterprint('Analyzing {} data ...'.format(this_test))
    # Load in the data
    all_times = {}
    for filename in data_filenames:
        if re.search('class=True', filename):
            key = 'CLASS'
        else:
            key = 'no CLASS'
        if re.search('compiled=True', filename):
            key += ', compiled'
        else:
            key += ', not compiled'
        all_times[key] = np.loadtxt(filename)
    # Plot the data
    fig_file = this_dir + '/result.png'
    plt.figure(figsize=(16, 12))
    markersize = 50
    for key, times in all_times.items():
        plt.loglog(scale_factors, times, '.',
                   markersize=markersize,
                   alpha=1.0,
                   label=key)
        markersize -= 10
    plt.xlim(a_begin, 1)
    plt.xlabel('$a$')
    plt.ylabel(r'$t\,\mathrm{{[{}]}}$'.format(unit_time))
    # Using CLASS or not makes a differnce at early times
    # due to the inclusion of e.g. radiation and neutrinos.
    # Find the latest time at which this difference is still important.
    rel_tol = 1e-2
    i = N_points
    for t1, t2 in zip(reversed(all_times[   'CLASS, compiled']),
                      reversed(all_times['no CLASS, compiled'])):
        i -= 1
        if not isclose(t1, t2, rel_tol=rel_tol):
            # Time found. Update plot.
            a = scale_factors[i]
            ylim = plt.gca().get_ylim()
            plt.loglog([a, a], ylim, 'k:', zorder=-1)
            plt.text(1.1*a, 0.4*ylim[1], r'$\leftarrow$ $1\%$ disagreement between' + '\n'
                                         r'$\leftarrow$ CLASS and no CLASS',
                     fontsize=16,
                     )
            plt.ylim(ylim)
            # If this time is too late, something is wrong
            a_max_allowed = 0.1
            if a > a_max_allowed:
                abort(f'A discrepency in t(a) of 1% between CLASS and the built-in '
                      f'Freedman equation is present as late as a = {a}, '
                      f'which is too extreme to be acceptable.\n'
                      f'See "{fig_file}" for a visualization.'
                      )
            break
    plt.legend(loc='best', fontsize=16).get_frame().set_alpha(0.7)
    plt.tight_layout()
    plt.savefig(fig_file)
    # Whether we are running in compiled mode or not
    # really should not make a big difference.
    # When using CLASS, a real (but still small) difference
    # appears because we are using cubic splines in compiled mode
    # and linear splines in pure Python mode. When not compiled,
    # the only difference is round-off errors.
    # Check that this is actually the case.
    rel_tol = 1e-5
    if not all(isclose(t1, t2, rel_tol=rel_tol)
               for t1, t2 in zip(all_times['CLASS, compiled'],
                                 all_times['CLASS, not compiled'])
               ):
        abort('The cosmic times computed via interpolation of CLASS data '
              'are different between compiled and pure Python mode.\n'
              f'See "{fig_file}" for a visualization.'
              )
    rel_tol = 1e+3*machine_ϵ
    if not all(isclose(t1, t2, rel_tol=rel_tol)
               for t1, t2 in zip(all_times['no CLASS, compiled'],
                                 all_times['no CLASS, not compiled'])
               ):
        abort('The cosmic times computed via the simple Friedmann equation '
              'are different between compiled and pure Python mode.\n'
              f'See "{fig_file}" for a visualization.'
              )
    masterprint('done')
