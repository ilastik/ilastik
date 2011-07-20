import glob, os
tests=glob.glob('tests/*.py')


excludeList=['test_context_star_2d.py']


def do(testname):
    if testname not in excludeList:
        cmd = "cd tests && python " + test
        if os.system(cmd):
            raise RuntimeError, "fail to execute " + testname
    else:
        print "#####################skipping test: " + testname

for test in tests:
    print "#######################executing test: " + test
    folder,test=os.path.split(test)
    do(test)
