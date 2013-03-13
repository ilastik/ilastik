# FIXME: use ilastik config file

compress_labels = False

# all these features are precalculated in opExtractObjects
vigra_features = ['Count', 'Mean', 'Variance', 'Skewness', 'Kurtosis']
more_features = []

# only these features are used. eventually these will be chosen
# interactively. They many include features not in 'vigra_features',
# in the case that some other features are also used.
selected_features = ['Count', 'Mean_obj', 'Mean_excl', 'Variance_obj', \
                     'Variance_excl', 'Skewness_obj', 'Skewness_excl', \
                      'Kurtosis_obj', 'Kurtosis_excl', 'lbp_excl', 'lbp_obj']
