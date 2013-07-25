#!/bin/bash -v

rm -rf /tmp/cylemon
git clone http://github.com/cstraehl/cylemon.git /tmp/cylemon

cd /tmp/cylemon
python setup.py config
python setup.py build
sudo python setup.py install


