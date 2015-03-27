"""
We want to always keep our GUI separate from all "headless mode" functionality.
In fact, if the user only needs headless mode, there should be no need to have GUI libraries (like PyQt4) installed at all.
Applet GUI classes should never be imported at module scope: they should be imported "just in time" in the functions that need them.

To help us developers keep good hygiene when it comes to GUI imports, this module is used to override PyQt4 in headless mode.
(See ilastik_main.py)
"""
raise Exception("Developer error: When ilastik is running in headless mode, you aren't allowed to import PyQt4.")

