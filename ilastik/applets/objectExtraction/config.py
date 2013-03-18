# FIXME: use ilastik config file

compress_labels = False

# all these features are precalculated in opExtractObjects
vigra_features = ['Count', 'Mean', 'Variance', 'Skewness', 'Kurtosis', 'Histogram']
other_features = ['lbp_obj', 'lbp_incl', 'lbp_excl', 'bad_slices']

# only these features are used. eventually these will be chosen
# interactively. They many include features not in 'vigra_features',
# in the case that some other features are also used.
selected_features = ['Count', 'Mean_obj', 'Mean_excl', 'Variance_obj', \
                     'Variance_excl', 'Skewness_obj', 'Skewness_excl', \
                      'Kurtosis_obj', 'Kurtosis_excl', 'lbp_obj', 'lbp_excl']

#selected_features = ['lbp_excl', 'lbp_obj']

#selected_features = ['Histogram_excl', 'Histogram_obj', 'lbp_excl', 'lbp_obj']
