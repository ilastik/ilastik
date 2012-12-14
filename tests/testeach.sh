#!/bin/bash

NOSE_ARG=${1-"."}

for f in `find $NOSE_ARG -iname "*test*.py"`
do
  echo "Running $f"; python ./nose_single.py --nologcapture $f
  RETVAL=$?
  [ $RETVAL -ne 0 ] && exit $RETVAL
done
