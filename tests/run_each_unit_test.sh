#!/bin/bash

#
# The ilastik test suite shouldn't be run from the standard 'nosetests' command, 
#  because some of the tests (GUI tests) can't be run that way.
#  (It has to do with the fact that these tests need to take control of the main thread, 
#  which means nosetests must be running in a separate thread.)
# 
# This simple bash script runs all tests in the current directory:
# - Only runs files with the word 'test' in their name
# - For files with 'gui' in the filename, the file is run directly
# - For all other files, the special 'nose_single' helper script is used.
#

TESTS_DIR=`dirname $0`
NOSE_ARG=${1-$TESTS_DIR}

SKIP_GUI_TESTS=${SKIP_GUI_TESTS-0}

for f in `find $NOSE_ARG -iname "*test*.py" | grep -v nanshe` 
do
  if echo $f | grep -q "testPixelClassificationBenchmarking.py"; then
      echo "Skipping $f because is takes too long"
      continue
  fi

  if echo $f | grep -q "testAutocontextGui.py"; then
      echo "Skipping $f which is known to fail"
      continue
  fi

  if echo $f | grep -q "testObjectCountingDrawing.py"; then
      echo "Skipping $f because for some reason it doesn't work in this script."
      continue
  fi

  if [ $SKIP_GUI_TESTS -ne 0 ]; then
      if echo $f | grep -iq "gui"; then
	  continue
      fi
  fi

  echo "Running $f"
  if echo $f | grep -iq "gui"; then
      # We assume that GUI tests have been set up to be run via 'if name == main' sections.
      python $f
  else
      python $TESTS_DIR/nose_single.py --nologcapture $f
  fi
  
  RETVAL=$?
  if [[ $RETVAL -ne 0 ]]; then
    exit $RETVAL
  fi
done
