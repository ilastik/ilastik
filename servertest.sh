#!/bin/bash

set -e
set -u
set -o pipefail
set -x

#RAW_DATA_ID="$(curl -s \
#               -F 'raw_data=@/home/tomaz/ilastikTests/SampleData/c_cells/cropped/cropped1.png' \
#               http://localhost:5000/data_sources)"
RAW_DATA_ID=123123
ANNOTATION_ID="$(curl -v --trace-ascii - \
                -F 'raw_data=@/home/tomaz/ilastikTests/SampleData/c_cells/cropped/cropped1_10_annotations_offset_by_188_124.png' \
                -F 'location={"x":188, "y":124, "z":0, "c":0, "t":0}' \
                -F "data_source_id=$RAW_DATA_ID" \
                http://localhost:5000/annotations)"

exit 1

HESSIAN_ID="$(curl -s \
               -F 'extractor_params={"sigma": 1.5};type=application/json' \
               http://localhost:5000/feature_extractors/hessian_of_gaussian)"

GAUSSIAN_ID="$(curl -s \
               -F 'extractor_params={"sigma": 0.3};type=application/json' \
               http://localhost:5000/feature_extractors/gaussian_smoothing)"

curl -s http://localhost:5000/feature_extractors

CLASSIFIER_ID="$(curl -s \
                      -F "annotation_ids=[$ANNOTATION_ID];type=application/json" \
                      -F "feature_extractor_ids=[$HESSIAN_ID, $GAUSSIAN_ID];type=application/json" \
                       http://localhost:5000/pixel_classifier)"
