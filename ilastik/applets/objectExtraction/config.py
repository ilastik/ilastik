# FIXME: use ilastik config file

compress_labels = False

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
