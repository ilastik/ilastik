"""
We want to always keep our GUI separate from all "headless mode" functionality.
In fact, if the user only needs headless mode, there should be no need to have GUI libraries (like PyQt5) installed at all.
Applet GUI classes should never be imported at module scope: they should be imported "just in time" in the functions that need them.

To help us developers keep good hygiene when it comes to GUI imports, this module is used to override PyQt5 in headless mode.
(See ilastik_main.py)
"""
# you can add this for debugging purposes. Since vigra tries to import pylab,
# which in turn tries to import PyQt5 this will be hit in every headless run and
# therefore produce noise that is unwanted
# from traceback import print_stack
# print_stack()
raise Exception("Developer error: When ilastik is running in headless mode, you aren't allowed to import PyQt5.")
