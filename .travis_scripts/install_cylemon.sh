#!/bin/bash -v

rm -rf /tmp/cylemon
git clone http://github.com/cstraehl/cylemon.git /tmp/cylemon

export VIRTUAL_ENV=$1
echo "VIRTUAL_ENV is $VIRTUAL_ENV"

export PATH=$VIRTUAL_ENV/bin:$PATH
export LD_LIBRARY_PATH=$VIRTUAL_ENV/lib:$LD_LIBRARY_PATH

cd /tmp/cylemon
python setup.py config
python setup.py build
sudo python setup.py install


