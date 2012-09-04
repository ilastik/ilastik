import os

# Travis-CI auto-discovers this package, but cylemon isn't installed on our travis setup yet. 
if os.getenv('TRAVIS') is None:
    from seededWatershedApplet import *
