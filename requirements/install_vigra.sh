#!/bin/sh

git clone http://github.com/ukoethe/vigra /tmp/vigra
mkdir -p /tmp/vigra/build
cd /tmp/vigra/build

export PATH=$VIRTUAL_ENV/bin:$PATH
export LD_LIBRARY_PATH=$VIRTUAL_ENV/lib:$LD_LIBRARY_PATH

cmake ..
make install


