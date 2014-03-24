# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# Copyright 2011-2014, the ilastik developers

# FIXME: use ilastik config file
compress_labels = False
'''
# all these features are precalculated in opExtractObjects
#vigra_features = ['Count', 'Mean', 'Variance', 'Skewness', 'Kurtosis', 'RegionCenter', 'RegionAxes']
vigra_features = ['Count', 'Mean']
other_features = []

#vigra_features = ['Count', 'Mean']
#other_features = []

# only these features are used. eventually these will be chosen
# interactively. They many include features not in 'vigra_features',
# in the case that some other features are also used.
#selected_features = ['Count', 'Mean', 'Mean_excl', 'Variance', \
#                     'Variance_excl', 'Skewness', 'Skewness_excl', \
#                      'Kurtosis', 'Kurtosis_excl']
selected_features = ['Count', 'Mean']
has_skimage = True
try:
    import skimage.feature
except:
    has_skimage = False
    print "scikit-image is not installed, some features disabled"
if not has_skimage:
    selected_features = [feature for feature in selected_features if "lbp" not
                         in feature]

#selected_features = ['lbp_excl', 'lbp_obj']

#selected_features = ['Histogram_excl', 'Histogram_obj', 'lbp_excl', 'lbp_obj']
'''
