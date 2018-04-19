import os
import zipfile

assert len([proj for proj in os.listdir('.') if proj.endswith('.ilp')]) == \
    31, 'unpack existing projects first in order not to overwrite them'

projects = zipfile.ZipFile('test_projects.zip',
                           mode='w',
                           compression=zipfile.ZIP_DEFLATED)

for name in os.listdir('.'):
    if name.endswith('.ilp'):
        projects.write(name)
        print('zipped ' + name)
