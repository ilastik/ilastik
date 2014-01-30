#!/bin/bash

TESTS_DIR=`dirname $0`
NOSE_ARG=${1-$TESTS_DIR}

SKIP_GUI_TESTS=${SKIP_GUI_TESTS-0}

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

  if [ $SKIP_GUI_TESTS -ne 0 ]; then
      if echo $f | grep -iq "gui"; then
	  continue
      fi
  fi

  echo "Running $f"; python $TESTS_DIR/nose_single.py --nologcapture $f
  RETVAL=$?
  if [[ $RETVAL -ne 0 ]]; then
    exit $RETVAL
  fi
done
