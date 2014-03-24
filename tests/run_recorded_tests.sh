#!/bin/bash

NOSE_ARG=${1-"."}

echo "BEGIN RECORDED TESTS"

for f in `find $NOSE_ARG -iname "*.py" | grep recorded_test_cases`
do
  if [[ `whoami` = "vagrant" ]]
  then
    # On the ilastik-test-vm, we clean the environment to ensure reproducibility of test runs.
    echo "Cleaning preferences file..."
    rm -f ~/.ilastik_preferences
  fi
  echo "Running recorded test: $f"; python ../ilastik.py --playback_script=$f --exit_on_failure --exit_on_success
  RETVAL=$?
  if [[ $RETVAL -ne 0 ]]; then
    exit $RETVAL
  fi
done
