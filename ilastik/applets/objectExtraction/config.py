# FIXME: use ilastik config file

compress_labels = True

# all these features are precalculated in opExtractObjects
vigra_features = ['Count', 'RegionCenter', 'Mean', 'Variance', 'Coord<ValueList>', \
                  'RegionRadii']

# only these features are used. eventually these will be chosen
# interactively. They many include features not in 'vigra_features',
# in the case that some other features are also used.
selected_features_division_detection = ['SquaredDistance01', 'SquaredDistance02', \
                     'SquaredDistance00', 'AngleDaughters', 'ChildrenSizeRatio', \
                     'SquaredDistanceRatio', 'Count', \
                     'ParentChildrenSizeRatio', 'Mean', 'Variance', 'ChildrenMeanRatio', \
                     'ParentChildrenMeanRatio',\
                     'SquaredDistance01_corr', 'SquaredDistance02_corr', \
                     'SquaredDistance00_corr', 'AngleDaughters_corr', 'ChildrenSizeRatio_corr', \
                     'SquaredDistanceRatio_corr', \
                     'ParentChildrenSizeRatio_corr', 'ChildrenMeanRatio_corr', \
                     'ParentChildrenMeanRatio_corr']

selected_features_cell_classification = ['Count', 'Mean', 'Variance', \
                     'RegionRadii']

selected_features = []
