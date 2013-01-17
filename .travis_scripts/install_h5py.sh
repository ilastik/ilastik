#!/bin/sh

hg clone https://code.google.com/p/h5py/ /tmp/h5py

cd /tmp/h5py/h5py
python api_gen.py

cd /tmp/h5py
python setup.py build
python setup.py install

