#
# Given the location of CPLEX static libraries, convert them to shared 
# libraries and install them into the ilastik-release/lib directory.
#

#
# Check usage
#
if [ $# != 2 ]; then
    if [ `uname` == "Darwin" ]; then
        echo "Usage: $0 <cplex-root-dir> <path/to/ilastik-1.X.Y-OSX.app>" 1>&2
    else
        echo "Usage: $0 <cplex-root-dir> <path/to/ilastik-1.X.Y-Linux>" 1>&2
    fi
    exit 1
fi

#
# Read args
#
CPLEX_ROOT_DIR="$1"
if [ `uname` == "Darwin" ]; then
    ILASTIK_RELEASE_DIR="$2/Contents/ilastik-release"
else
    ILASTIK_RELEASE_DIR="$2"
fi

#
# Validate args
#
if [ ! -d "$CPLEX_ROOT_DIR/cplex" ]; then
    echo "Error: $CPLEX_ROOT_DIR does not appear to be the CPLEX installation directory." 1>&2
    exit 2
fi

if [ ! -d "$ILASTIK_RELEASE_DIR/lib" ]; then
    echo "Error: $ILASTIK_RELEASE_DIR does not appear to be an ilastik installation directory." 1>&2
    exit 2
fi


CPLEX_LIB_DIR=`echo $CPLEX_ROOT_DIR/cplex/lib/x86-64*/static_pic`
CONCERT_LIB_DIR=`echo $CPLEX_ROOT_DIR/concert/lib/x86-64*/static_pic`

#
# Are we using clang?
#
g++ 2>&1 | grep clang > /dev/null
GREP_RESULT=$?
if [ $GREP_RESULT == 0 ]; then
    # Using clang, must specify libstdc++ (not libc++, which is the default).
    STDLIB_ARG="-stdlib=libstdc++"
else
    STDLIB_ARG=""
fi

#
# Create a shared library from each static cplex library.
#
if [ `uname` == "Darwin" ]; then
    g++ -fpic -shared -Wl,-all_load ${CPLEX_LIB_DIR}/libcplex.a     $STDLIB_ARG -o ${ILASTIK_RELEASE_DIR}/lib/libcplex.dylib    -Wl,-no_compact_unwind -Wl,-install_name,@loader_path/libcplex.dylib -L${ILASTIK_RELEASE_DIR}/lib
    g++ -fpic -shared -Wl,-all_load ${CONCERT_LIB_DIR}/libconcert.a $STDLIB_ARG -o ${ILASTIK_RELEASE_DIR}/lib/libconcert.dylib  -Wl,-no_compact_unwind -Wl,-install_name,@loader_path/libconcert.dylib -L${ILASTIK_RELEASE_DIR}/lib
    g++ -fpic -shared -Wl,-all_load ${CPLEX_LIB_DIR}/libilocplex.a  $STDLIB_ARG -o ${ILASTIK_RELEASE_DIR}/lib/libilocplex.dylib -Wl,-no_compact_unwind -Wl,-install_name,@loader_path/libilocplex.dylib \
        -L${ILASTIK_RELEASE_DIR}/lib -lcplex -lconcert
else
    g++ -fpic -shared -Wl,-whole-archive ${CPLEX_LIB_DIR}/libcplex.a     -Wl,-no-whole-archive -o ${ILASTIK_RELEASE_DIR}/lib/libcplex.so
    g++ -fpic -shared -Wl,-whole-archive ${CONCERT_LIB_DIR}/libconcert.a -Wl,-no-whole-archive -o ${ILASTIK_RELEASE_DIR}/lib/libconcert.so
    g++ -fpic -shared -Wl,-whole-archive ${CPLEX_LIB_DIR}/libilocplex.a  -Wl,-no-whole-archive -o ${ILASTIK_RELEASE_DIR}/lib/libilocplex.so
fi

echo "Done installing the CPLEX libraries into ilastik." 1>&2