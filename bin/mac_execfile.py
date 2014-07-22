"""
This script simply executes the python file provided as the first argument.  
It basically provides the same functionality as the normal python interpreter, but without many of the options python provides.

It is useful as a means to execute arbitrary scripts in the mac binary.  
This file is passed to py2app via the --extra-scripts option, and then arbitrary scripts can be launched with the same environment that the ilastik app uses.
(Note that the interpreter located in ilastik.app/Contents/MacOS/python does NOT properly set up the environment.)
"""
if __name__ == "__main__":
    import os
    import sys

    # Read the file to execute
    f = sys.argv[1]
    
    # Remove this file from the list, so that sys.argv[0] is the name of the file we're executing.
    sys.argv.pop(0)
    __file__ = f
    
    # By default, this script is always launched with a CWD of ilastik.app/Contents/Resources.
    # But that's confusing, so switch back to the CWD of the terminal when the script was launched.
    original_cwd = os.environ['PWD']
    os.chdir(original_cwd)
    
    # Execute the script with execfile.  This way, if __name__ == '__main__' sections should work.
    execfile(f)
