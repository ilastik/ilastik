import glob, os


tests=glob.glob('tests/*.py')  #List of all tests

excludeList=['test_context_star_2d.py']  #exclude some test 
swaplist=[('graph_save.py','graph_load.py')] #Tuples of tests that have to be executed exactly in this order



def swap(list):
    for tuple in list:
        test1,test2=tuple
        test1,test2=os.path.join('tests',test1),os.path.join('tests',test2)
        a,b=tests.index(test1),tests.index(test2)
        
        if b<a:
            tests[b], tests[a] = tests[a], tests[b]


swap(swaplist)    

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
    
print "########### ALL TESTS ARE DONE, YOU DID NOT BREAK ANYTHING TODAY !#############"

