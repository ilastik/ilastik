# FIXME: use ilastik config file

compress_labels = True

# all these features are precalculated in opExtractObjects
vigra_features = ['Count']

# only these features are used. eventually these will be chosen
# interactively. They many include features not in 'vigra_features',
# in the case that some other features are also used.
selected_features = ['Count']
