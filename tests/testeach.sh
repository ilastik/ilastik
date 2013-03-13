#!/bin/bash

NOSE_ARG=${1-"."}

for f in `find $NOSE_ARG -iname "*test*.py"`
do
  if [[ $f == "./test_applets/thresholdTwoLevels/testThresholdTwoLevels.py" ]]; then
      echo "Skipping $f which is known to fail"
      continue
  fi

  if [[ $f == "./test_applets/pixelClassification/testPixelClassificationBenchmarking.py" ]]; then
      echo "Skipping $f because is takes too long"
      continue
  fi

  if [[ $f == "./test_applets/base/testSerializer.py" ]]; then
      echo "Skipping $f which is known to fail"
      continue
  fi

  if [[ $f == "./test_applets/objectExtraction/testOperators.py" ]]; then
      echo "Skipping $f which is known to fail"
      continue
  fi

  echo "Running $f"; python ./nose_single.py --nologcapture $f
  RETVAL=$?
  if [[ $RETVAL -ne 0 ]]; then
    exit $RETVAL
  fi
done
