import glob, os
tests=glob.glob('tests/*.py')


excludeList=['write some files to skip']


def do(testname):
    if testname not in excludeList:
        cmd = "cd tests && python " + test
        if os.system(cmd):
            raise

for test in tests:
    folder,test=os.path.split(test)
    do(test)
