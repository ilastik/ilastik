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
