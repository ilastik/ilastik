#!/bin/bash

# Usage: run_each_unit_test.sh <dir> [first-nonskipped-test]
# 
# Run all the tests in the given directory.  
# If a first-nonskipped-test is given, then skip all tests until that 
#  file is found, then resume testing.
#
# The ilastik test suite shouldn't be run from the standard 'pytest' command,
#  because some of the tests (GUI tests) can't be run that way.
#  (It has to do with the fact that these tests need to take control of the main thread, 
#  which means tests must be running in a separate thread.)
# 
# This simple bash script runs all tests in the current directory:
# - Only runs files with the word 'test' in their name
# - For files with 'gui' in the filename, the file is run directly
# - For all other files, the special 'run_single' helper script is used.
#

TESTS_DIR=`dirname $0`
DIR_ARG=${1-$TESTS_DIR}

SKIP_GUI_TESTS=${SKIP_GUI_TESTS-0}

SKIP_UNTIL=${2-"RUN_ALL"}

FAILURES=0
BROKEN=()


for f in `find $DIR_ARG -iname "*test*.py"`
do
  if echo $f | grep -q "shellGuiTestCaseBase.py\|generate_test_data.py"; then
      # This isn't a test case, it's a helper file
      continue
  fi

  if echo $f | grep -q "testPixelClassificationBenchmarking.py"; then
      echo "Skipping $f because is takes too long"
      continue
  fi

  if echo $f | grep -q "testAutocontextGui.py"; then
      echo "Skipping $f which is known to fail"
      continue
  fi

  if echo $f | grep -q "testObjectCountingMultiImageGui.py"; then
      echo "Skipping $f because it fails too often, without a real reason."
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
  elif echo $f | grep -q "testPixelClassificationHeadless.py"; then
      python $f
  else
      python $TESTS_DIR/run_single.py $f --capture=no
  fi
  
  RETVAL=$?
  if [[ ${RETVAL} -ne 0 ]]; then
    if [[ ${CONTINUE_ON_FAILURE} -lt 1 ]]; then
      echo "Encountered a failure, exiting right away:"
      echo "In order to continue testing set CONTINUE_ON_FAILURE=1"
      exit ${RETVAL}
    fi
    ((FAILURES+=1))
    BROKEN+=($f)
  fi
done


if [[ ${FAILURES} -ne 0 ]]; then
  echo "Encountered ${FAILURES} failures in the following files:"
  for f in ${BROKEN[@]}
  do
    echo $f
  done

  exit ${FAILURES}
fi
