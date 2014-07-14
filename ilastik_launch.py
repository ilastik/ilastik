def ilastik_main():
    import os, sys
    ilastik_dir = os.path.abspath(os.path.dirname(sys.argv[0])+"\\..\\..")
    print 'Loading ilastik from "%s".' % ilastik_dir
    
    # remove undesired paths from PYTHONPATH and add ilastik's submodules
    pythonpath = [k for k in sys.path if k.startswith(ilastik_dir)]
    for k in ['\\ilastik\\lazyflow', '\\ilastik\\volumina', '\\ilastik\\ilastik']:
        pythonpath.append(ilastik_dir+k)
    sys.path = pythonpath
    
    # empty PATH except for gurobi and CPLEX and add ilastik's installation paths
    path = [k for k in os.environ.get('PATH').split(os.pathsep) \
               if k.count('CPLEX') > 0 or k.count('gurobi') > 0]
    for k in ['\\Qt4\\bin', '\\python', '\\bin']:
        path.append(ilastik_dir+k)
    os.environ['PATH'] = os.pathsep.join(reversed(path))
    
    # parse args and start ilastik
    import ilastik_main
    import ilastik.monkey_patches
    ilastik.monkey_patches.extend_arg_parser(ilastik_main.parser)

    parsed_args, workflow_cmdline_args = ilastik_main.parser.parse_known_args()
    
    # allow to start-up by double-clicking an '.ilp' file
    if len(workflow_cmdline_args) == 1 and \
       workflow_cmdline_args[0].endswith('.ilp') and \
       parsed_args.project is None:
            parsed_args.project = workflow_cmdline_args[0]
            workflow_cmdline_args = []

    # DEBUG EXAMPLES
    #parsed_args.project='/Users/bergs/MyProject.ilp'
    #parsed_args.headless = True

    ilastik_main.main(parsed_args, workflow_cmdline_args)

if __name__ == '__main__':
    ilastik_main()
