# FIXME: use ilastik config file

compress_labels = True

# all these features are precalculated in opExtractObjects
vigra_features = ['Count','RegionCenter', 'Mean', 'Variance']

# only these features are used. eventually these will be chosen
# interactively. They many include features not in 'vigra_features',
# in the case that some other features are also used.
selected_features = ['SquaredDistance01', 'SquaredDistance02', \
                     'SquaredDistance00', 'AngleDaughters', 'ChildrenSizeRatio', \
                     'SquaredDistanceRatio', 'Count', \
                     'ParentChildrenSizeRatio', 'Mean', 'Variance', 'ChildrenMeanRatio', \
                     'ParentChildrenMeanRatio']
