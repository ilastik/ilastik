================================================
Nice to know
================================================

Facts that are nice to know and that can improve your own workflow


Load a particular ilastik project at each startup of ilastik
=============================================================================

How can you make a project getting loaded at each startup of ilastik?

Therefore you have to open the **ilastik.py** file in your root directory and look into the method **main**:


Then add a line like many other people did before you in the DEVELOPERS section:

.. code::

    parsed_args.project='/path/to/my/project/MyProject.ilp'



Export slot diagrams
=======================

Exporting slot diagrams is important to see in a very fast way to see which slots is

* ready (**white**)
* not ready (**red**)
* not ready but optional (**blue**)

For more information on whether a slot is of level 0, 1 or something else, see the `Lazyflow Documentation <http://ilastik.org/lazyflow/advanced.html#higher-level-slots>`_.

Start ilastik in debug mode, (e.g. ./run_ilastik.py --debug) and go to the applet you want to analyze.
Then look at the top tabs, like Project, Settings, View, Debug, Help ...

Click Debug and 

* **Export Operator Diagram - Unlimited** to get the applet operator diagram
* **Export Workflow Diagram - Unlimited** to get the operator diagram of the whole workflow


Getting all input and/or output slots
==================================================

In the opXXXX.py, you can put this at the very end of your init to list all slots and work elsewhere with it

.. code::

        for slot in self.inputs.values() + self.outputs.values():
            #if slot.level == 0 or slot.level == 1:
            if slot._type == "output":
                print slot.name
            else:
                print "input: " + slot.name



