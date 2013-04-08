#!/bin/bash

if [ $# -ne 1 ]
then
  echo "Expected exactly one arg: the directory to search"
  exit 1
fi

for f in `find $1 -name "*.py"`;
do
  echo "Running $f"
  python launch_workflow.py --workflow=PixelClassificationWorkflow --playback_script=$f --playback_speed=2.0 --exit_on_failure --exit_on_success
  RETVAL=$?
  if [[ $RETVAL -ne 0 ]]; then
    exit $RETVAL
  fi
done
