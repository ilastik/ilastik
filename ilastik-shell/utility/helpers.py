import os

def getPathToLocalDirectory(sourcePath):
    # Determines the path of this python file so we can refer to other files relative to it.
    p = os.path.split(sourcePath)[0]+'/'
    if p == "/":
        p = "."+p
    return p
