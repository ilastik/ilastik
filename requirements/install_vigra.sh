#!/bin/bash -v

git clone http://github.com/ukoethe/vigra /tmp/vigra
mkdir -p /tmp/vigra/build
cd /tmp/vigra/build

export VIRTUAL_ENV=$1
echo "VIRTUAL_ENV is $VIRTUAL_ENV"

export PATH=$VIRTUAL_ENV/bin:$PATH
export LD_LIBRARY_PATH=$VIRTUAL_ENV/lib:$LD_LIBRARY_PATH

cmake -DEPENDENCY_SEARCH_PREFIX=$VIRTUAL_ENV ..
make install


