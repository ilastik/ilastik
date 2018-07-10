
def fill_feature_description(features):

        for feature in features.keys():
            features[feature]["displaytext"] = feature
            features[feature]["detailtext"] = feature + ", stay tuned for more details"
            features[feature]["advanced"] = False
            features[feature]["group"] = "Shape"

            if feature == "InputVolume":
                features[feature]["displaytext"] = "Object Area"
                features[feature]["detailtext"] = "Area of this object, computed from the interpixel contour " \
                                                  " (can be slightly larger than simple size of the object in pixels). " \
                                                  "This feature is used to compute convexity."

            if feature == "HullVolume":
                features[feature]["displaytext"] = "Convex Hull Area"
                features[feature]["detailtext"] = "Area of the convex hull of this object"

            if feature == "Convexity":
                features[feature]["displaytext"] = "Convexity"
                features[feature]["detailtext"] = " The ratio between the areas of the object and its convex hull (<= 1)"

            if feature == "DefectVolumeMean":
                features[feature]["displaytext"] = "Mean Defect Area"
                features[feature]["detailtext"] = "Average of the areas of convexity defects. Defects are defined as connected components in the area of the " \
                                                  "convex hull, not covered by the original object."

            if feature == "DefectVolumeVariance":
                features[feature]["displaytext"] = "Variance of Defect Area"
                features[feature]["detailtext"] = "Variance of the distribution of areas of convexity defects. Defects are defined as connected components in the area of the " \
                                                  "convex hull, not covered by the original object."
            if feature == "DefectVolumeSkewness":
                features[feature]["displaytext"] = "Skewness of Defect Area"
                features[feature]["detailtext"] = "Skewness (3rd standardized moment, measure of asymmetry) of the distribution of the areas of convexity defects. " \
                                                  "Defects are defined as connected components in the area of the " \
                                                  "convex hull, not covered by the original object."

            if feature == "DefectVolumeKurtosis":
                features[feature]["displaytext"] = "Kurtosis of Defect Area"
                features[feature]["detailtext"] = "Kurtosis (4th standardized moment, measure of tails' heaviness) of the distribution of the areas of convexity defects. " \
                                                  "Defects are defined as connected components in the area of the " \
                                                  "convex hull, not covered by the original object."

            if feature == "DefectCount":
                features[feature]["displaytext"] = "Number of Defects"
                features[feature]["detailtext"] = "Total number of defects, i.e. number of connected components in the area of the " \
                                                  "convex hull, not covered by the original object"

            if feature == "DefectDisplacementMean":
                features[feature]["displaytext"] = "Mean Defect Displacement"
                features[feature]["detailtext"] = "Mean distance between the centroids of the original object and the centroids of the defects, weighted by defect area."

            if feature == "InputCenter":
                features[feature]["displaytext"] = "Object Center"
                features[feature]["detailtext"] = "Centroid of this object. The axes order is x, y, z"
                features[feature]["group"] = "Location"

            if feature == "HullCenter":
                features[feature]["displaytext"] = "Convex Hull Center"
                features[feature]["detailtext"] = "Centroid of the convex hull of this object. The axes order is x, y, z"
                features[feature]["group"] = "Location"

            if feature == "DefectCenter":
                features[feature]["displaytext"] = "Defect Center"
                features[feature]["detailtext"] = "Combined centroid of convexity defects, which are defined as areas of the " \
                                                  "convex hull, not covered by the original object."
                features[feature]["group"] = "Location"

        return features
