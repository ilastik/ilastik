#!/bin/bash

NOSE_ARG=${1-"."}

for f in `find $NOSE_ARG -iname "*test*.py"`
do
  if echo $f | grep -q "testPixelClassificationBenchmarking.py"; then
      echo "Skipping $f because is takes too long"
      continue
  fi

  if echo $f | grep -q "testAutocontextGui.py"; then
      echo "Skipping $f which is known to fail"
      continue
  fi

  echo "Running $f"; python ./nose_single.py --nologcapture $f
  RETVAL=$?
  if [[ $RETVAL -ne 0 ]]; then
    exit $RETVAL
  fi
done
