Troubleshooting
====================================

* When you run ilastik and read in images and you get the following message:

        .. code::

                libGL error: unable to load driver: i965_dri.so
                libGL error: driver pointer missing
                libGL error: failed to load driver: i965
                libGL error: unable to load driver: i965_dri.so
                libGL error: driver pointer missing
                libGL error: failed to load driver: i965
                libGL error: unable to load driver: swrast_dri.so
                libGL error: failed to load driver: swrast

        The following workaround worked for me:
        .. code::

                cd ~/miniconda2/envs/ilastik-devel/lib/
                mv libstdc++.so{,.bak}
                mv libstdc++.so.6{,.bak}
                mv libstdc++.so.6.0.19{,.bak}
                ln -s /usr/lib/libstdc++.so .

* 
        .. code::

                
            self.inputs[slot.name] = slot[index]
            File "~/miniconda2/envs/ilastik-devel/ilastik-meta/lazyflow/lazyflow/slot.py", line 968, in __getitem__
            return self._subSlots[key]
                IndexError: list index out of range

   Then check your workflow, whether the errorous applet is correctly integrated

*

        .. code::

                File "~/miniconda2/envs/ilastik-devel/lib/python2.7/site-packages/h5py/_hl/dataset.py", line 93, in make_new_dset
                tid = h5t.py_create(dtype, logical=1)
                File "h5py/h5t.pyx", line 1450, in h5py.h5t.py_create (-------src-dir-------/h5py/h5t.c:16211)
                File "h5py/h5t.pyx", line 1470, in h5py.h5t.py_create (-------src-dir-------/h5py/h5t.c:16042)
                File "h5py/h5t.pyx", line 1525, in h5py.h5t.py_create (-------src-dir-------/h5py/h5t.c:15944)
                TypeError: Object dtype dtype('O') has no native HDF5 equivalent

                ERROR 2017-01-10 15:51:25,204 log_exception 20991 140606414022400 Project Save Action failed due to the exception shown above.


        Then it is possible, that an operator was set with an invalid value, like a QString. 
        Conversion to string may help:

        .. code::

                op.MyOperator.setValue( str( self._labelControlUi.neighborsComboBox.itemText(index) ) )

                


