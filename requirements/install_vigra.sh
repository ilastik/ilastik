#!/bin/sh

#git clone http://github.com/ukoethe/vigra /tmp/vigra
mkdir /tmp/vigra/build
cd /tmp/vigra/build
cmake ..
make install
#make check

