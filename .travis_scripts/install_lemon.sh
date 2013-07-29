#!/bin/bash -v
rm -rf /tmp/lemon
hg clone http://lemon.cs.elte.hu/hg/lemon /tmp/lemon

mkdir -p /tmp/lemon/build
cd /tmp/lemon/build

export VIRTUAL_ENV=$1
echo "VIRTUAL_ENV is $VIRTUAL_ENV"

export PATH=$VIRTUAL_ENV/bin:$PATH
export LD_LIBRARY_PATH=$VIRTUAL_ENV/lib:$LD_LIBRARY_PATH

cmake \
    -DBUILD_SHARED_LIBS=yes \
    -DCMAKE_BUILD_TYPE=Release \
    ..

sudo make install

