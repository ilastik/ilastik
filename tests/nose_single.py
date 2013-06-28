import sys
import nose
import threading

from tests.helpers import mainThreadHelpers

# For some mysterious reason, we need to make sure that volumina.api gets imported 
#  from the main thread before nose imports it from a separate thread.
# If we don't, QT gets confused about which thread is really the main thread.
# This must be because the "main" thread is determined by some QT class or module 
#  that first becomes active somewhere in volumina, but I can't figure out which one it is.
#  Otherwise, I would just go ahead and import it now.
import volumina.api

if __name__ == "__main__":
#    sys.argv.append("test_applets/pixelClassification/testPixelClassificationGui.py")
#    sys.argv.append("--nocapture")
#    sys.argv.append("--nologcapture")
    if len(sys.argv) < 2:
        sys.stderr.write( "Usage: python {} FILE [--nocapture] [--nologcapture]\n".format(sys.argv[0]) )
        sys.exit(1)

    #
    # Run a SINGLE test file using nosetests, which is launched in a separate thread.
    # The main thread (i.e. this one) is left available for launching other tasks (e.g. the GUI).
    #    
    filename = sys.argv.pop(1)
    sys.exit(mainThreadHelpers.run_nosetests_in_separate_thread(filename))
