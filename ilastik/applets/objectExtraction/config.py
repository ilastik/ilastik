# FIXME: use ilastik config file
compress_labels = False
'''
# all these features are precalculated in opExtractObjects
'''

vigra_features = ['Count', 'RegionCenter', 'Mean', 'Variance', 'Coord<ValueList>', 'RegionRadii']
features_vigra_name = 'Vigra Object Features'

other_features = []

# only these features are used. eventually these will be chosen
# interactively. They many include features not in 'vigra_features',
# in the case that some other features are also used.
features_division_detection_name = 'Cell Division Features'
selected_features_division_detection = {}
selected_features_division_detection[features_division_detection_name] = ['SquaredDistance01', 'SquaredDistance02', \
                     'SquaredDistance00', 'AngleDaughters', 'ChildrenSizeRatio', 'SquaredDistanceRatio',  
                     'ParentChildrenSizeRatio', 'ChildrenMeanRatio', 'ParentChildrenMeanRatio',\
                     'SquaredDistance01_corr', 'SquaredDistance02_corr', \
                     'SquaredDistance00_corr', 'AngleDaughters_corr', 'ChildrenSizeRatio_corr', \
                     'SquaredDistanceRatio_corr', 'ParentChildrenSizeRatio_corr', 'ChildrenMeanRatio_corr', \
                     'ParentChildrenMeanRatio_corr']
selected_features_division_detection[features_vigra_name] = [ 'Count', 'Mean', 'Variance' ]


features_cell_classification_name = 'Cell Classification Features'
selected_features_cell_classification = {}
selected_features_cell_classification[features_vigra_name] = ['Count', 'Mean', 'Variance', 'RegionRadii' ]
#selected_features_cell_classification[features_cell_classification_name] = ['GMM_BIC']
selected_features_cell_classification[features_cell_classification_name] = [ ]


num_max_objects = 2