#!/bin/sh

git clone http://github.com/ukoethe/vigra /tmp/vigra
mkdir -p /tmp/vigra/build
cd /tmp/vigra/build

ENV_STRING='PATH=$VIRTUAL_ENV/bin:$PATH LD_LIBRARY_PATH=$VIRTUAL_ENV/lib:$LD_LIBRARY_PATH'
$ENV_STRING cmake ..
$ENV_STRING make install


