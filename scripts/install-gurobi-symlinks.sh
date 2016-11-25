#
# Given the location of a Gurobi installation,
# install symlinks to the gurobi shared libraries into the ilastik binary directory tree.
#

#
# Check usage
#
if [ $# != 2 ]; then
    if [ `uname` == "Darwin" ]; then
        echo "Usage: $0 <path/to/gurobi650/mac64> <path/to/ilastik-1.X.Y-OSX.app>" 1>&2
    else
        echo "Usage: $0 <path/to/gurobi650/linux64> <path/to/ilastik-1.X.Y-Linux>" 1>&2
    fi
    exit 1
fi

#
# Read args
#
GUROBI_ROOT_DIR="$1"
if [ `uname` == "Darwin" ]; then
    ILASTIK_RELEASE_DIR="$2/Contents/ilastik-release"
else
    ILASTIK_RELEASE_DIR="$2"
fi

#
# Validate args
#
if [ ! -e "$GUROBI_ROOT_DIR/bin/gurobi.sh" ]; then
    echo "Error: $GUROBI_ROOT_DIR does not appear to be the Gurobi installation directory." 1>&2
    exit 2
fi

if [[ "GUROBI_ROOT_DIR" =~ ( |\') ]]; then
    echo "Sorry, this script can't handle a Gurobi installation directory with spaces in the name." 1>&2
    exit 2
fi

if [ ! -d "$ILASTIK_RELEASE_DIR/lib" ]; then
    echo "Error: $ILASTIK_RELEASE_DIR does not appear to be an ilastik installation directory." 1>&2
    exit 2
fi


GUROBI_LIB_DIR=$(echo $GUROBI_ROOT_DIR/lib)

# Symlink the gurobi libraries into the lib directory
(
    cd "${ILASTIK_RELEASE_DIR}/lib"
    for f in $(ls "${GUROBI_LIB_DIR}"/*.so); do
        echo "Installing link to: ${f}"
        ln -f -s ${f}
    done
)

echo ""
echo "Done installing the Gurobi library symlinks into ilastik." 1>&2
