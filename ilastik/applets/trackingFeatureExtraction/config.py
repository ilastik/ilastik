# FIXME: use ilastik config file
compress_labels = False
'''
# all these features are precalculated in opExtractObjects
'''

vigra_features = ['Count', 'RegionCenter', 'Mean', 'Variance', 'RegionRadii', 'Maximum', 'Minimum', 'Skewness', 'Sum', 'Coord<Principal<Kurtosis>>', 'Coord<Principal<Skewness>>', 'Kurtosis']
features_vigra_name = 'Standard Object Features'

other_features = []

features_division_name = 'Cell Division Features'
selected_features_division = {}
division_features = ['ParentChildrenRatio_Count', 'ParentChildrenRatio_Mean', 'ChildrenRatio_Count', 'ChildrenRatio_Mean', \
                   'ParentChildrenAngle_RegionCenter', 'ChildrenRatio_SquaredDistances']

selected_features_division[features_division_name] = division_features
selected_features_division[features_vigra_name] = [ 'Count', 'Mean', 'Variance' ]

selected_features_objectcount = {}
selected_features_objectcount[features_vigra_name] = ['Count', 'Mean', 'Variance', 'RegionRadii' ]

# anisotropy scales
image_scale = [1.0, 1.0, 1.0]

# number of nearest successors considered for division features
n_best_successors = 3 

# name of region center feature at time t
com_name_cur = 'RegionCenter'

# name of region center feature at time t+1
com_name_next = 'RegionCenter'

# name of size feature
size_name = 'Count'

# deliminator for division feature concatenation
delim = '_'

# size of search window for successor candidates in t+1
template_size = 50

# do not consider objects with size < size_filter as children candidates
size_filter = 4 

# for every of the n_best_successors, set this value as default if no candidate is found in the search window
squared_distance_default = 9999
