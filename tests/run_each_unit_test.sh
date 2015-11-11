#!/bin/bash

# Usage: run_each_unit_test.sh <dir> [first-nonskipped-test]
# 
# Run all the tests in the given directory.  
# If a first-nonskipped-test is given, then skip all tests until that 
#  file is found, then resume testing.
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

SKIP_UNTIL=${2-"RUN_ALL"}

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

  if [[ "${SKIP_UNTIL}" != "RUN_ALL" ]]; then
      # Check if this is the file we're looking for.
      # If so, reset the SKIP_UNTIL variable so we run everything from now on.
      if echo $f | grep -q "${SKIP_UNTIL}"; then
	  SKIP_UNTIL="RUN_ALL"
      else
          # Still skipping
          echo "Skipping $f"
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
