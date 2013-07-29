#!/bin/bash -v

mkdir -p $HOME/tmp
rm -rf $HOME/tmp/cylemon
git clone http://github.com/cstraehl/cylemon.git $HOME/tmp/cylemon

export VIRTUAL_ENV=$1
echo "VIRTUAL_ENV is $VIRTUAL_ENV"

export PATH=$VIRTUAL_ENV/bin:$PATH
export LD_LIBRARY_PATH=$VIRTUAL_ENV/lib:$LD_LIBRARY_PATH

cd $HOME/tmp/cylemon
echo "*** setup.py config ***"
python setup.py config
echo "*** setup.py build ***"
python setup.py build
echo "*** setup.py install ***"
python setup.py install


