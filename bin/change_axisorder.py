import sys
import h5py

if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.stderr.write("Usage: {} project_file.ilp axisorder\n")
        sys.exit(1)
    
    projectfile = sys.argv[1]
    axisorder = sys.argv[2]

    with h5py.File(projectfile) as f:
        # Delete the old axisorder and replace it with our new one.
        try:
            del f['Input Data/infos/lane0000/Raw Data/axisorder']
        except KeyError:
            pass
        
        f['Input Data/infos/lane0000/Raw Data/axisorder'] = axisorder
        
        # If 'axistags' field is present, it overrides axisorder.
        # Delete it.
        try:
            del f['Input Data/infos/lane0000/Raw Data/axistags']
        except KeyError:
            pass
    
        # Delete the classifier so the project MUST be retrained.
        try:
            del f['PixelClassification/ClassifierForests']
        except KeyError:
            pass

    print "Done."
        