#!/bin/bash

#!/bin/bash
NOSE_ARG=${1-"."}

echo "BEGIN RECORDED TESTS"

for f in `find $NOSE_ARG -iname "*.py" | grep recorded_test_cases`
do
  echo "Running recorded test: $f"; python ilastik.py --playback_script=$f --exit_on_failure --exit_on_success
  RETVAL=$?
  if [[ $RETVAL -ne 0 ]]; then
    exit $RETVAL
  fi
done
