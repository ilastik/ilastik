#include <vigra/multi_array.hxx>
#include <vigra/tinyvector.hxx>
#include <vigra/numpy_array.hxx>
#include <vigra/numpy_array_converters.hxx>
#include <boost/python.hpp>
#include <vector>
#include <iostream>
#include <limits>

//#define DEBUG_PRINTING=1

//http://en.wikibooks.org/wiki/C%2B%2B_Programming/Templates/Template_Meta-Programming#Example:_Compile-time_.22If.22
template <bool Condition, typename TrueResult, typename FalseResult>
class if_;
 
template <typename TrueResult, typename FalseResult>
struct if_<true, TrueResult, FalseResult>
{
  typedef TrueResult result;
};
 
template <typename TrueResult, typename FalseResult>
struct if_<false, TrueResult, FalseResult>
{
  typedef FalseResult result;
};

typedef vigra::UInt16 coordinate_t;
typedef vigra::UInt32  weight_t;

enum StringStyle {TableStyle, MatrixStyle}; ///< Flag to be used with the member function asString() of View.

template<typename ARRAY>
void printArray(const ARRAY& a, std::string indent="") {
    std::ostringstream out(std::ostringstream::out);
    
    StringStyle style = MatrixStyle;
    typedef int coordinate_type;
    typedef typename ARRAY::const_iterator const_iterator;
    
    if(style == MatrixStyle) {
        if(a.actual_dimension == 0) {
            // scalar
            out << "A = " << a(0) << std::endl;
        }
        else if(a.actual_dimension == 1) {
            // vector
            out << "A = (";
            for(size_t j=0; j<a.size(); ++j) {
                out << a(j) << ", ";
            }
            out << "\b\b)" << std::endl;
        }
        else if(a.actual_dimension == 2) {
            // matrix
            if(true /* coordinateOrder_ == FirstMajorOrder */) {
                out << "A(r,c) =" << std::endl;
                for(size_t y=0; y<a.shape(0); ++y) {
                    for(size_t x=0; x<a.shape(1); ++x) {
                        out << a(y, x) << ' ';
                    }
                    out << std::endl;
                }
            }
            else {
                out << "A(c,r) =" << std::endl;
                for(size_t y=0; y<a.shape(1); ++y) {
                    for(size_t x=0; x<a.shape(0); ++x) {
                        out << a(x, y) << ' ';
                    }
                    out << std::endl;
                }
            }
        }
        else {
            // higher dimensional
            typename ARRAY::difference_type c1;
            unsigned short q = 2;
            if(true /* coordinateOrder_ == FirstMajorOrder */) {
                q = a.actual_dimension-3;
            }
            
            int i = 0;
            for(const_iterator it = a.begin(); it != a.end(); ++it, ++i) {
                typename ARRAY::difference_type c2 = a.scanOrderIndexToCoordinate(i);
                if(i == 0 || c2[q] != c1[q]) {
                    if(i != 0) {
                        out << std::endl << std::endl;
                    }
                    if(true /* coordinateOrder_ == FirstMajorOrder */) {
                        out << "A(";
                        for(size_t j=0; j<static_cast<size_t>(a.actual_dimension-2); ++j) {
                            out << c2[j] << ",";
                        }
                    }
                    else {
                        out << "A(c,r,";
                        for(size_t j=2; j<a.actual_dimension; ++j) {
                            out << c2[j] << ",";
                        }
                    }
                    out << '\b';
                    if(true /* coordinateOrder_ == FirstMajorOrder */) {
                        out << ",r,c";
                    }
                    out << ") =" << std::endl;
                }
                else if(c2[1] != c1[1]) {
                    out << std::endl;
                }
                out << *it << " ";
                c1 = c2;
            }
            out << std::endl;
        }
        out << std::endl;
    }
    else if(style == TableStyle) {
        if(a.actual_dimension == 0) {
            // scalar
            out << "A = " << a(0) << std::endl;
        }
        else {
            // non-scalar
            int j = 0;
            for(const_iterator it = a.begin(); it != a.end(); ++it, ++j) {
                out << "A(";
                typename ARRAY::difference_type c = a.scanOrderIndexToCoordinate(j);
                for(size_t j=0; j<c.size(); ++j) {
                    out << c[j] << ',';
                }
                out << "\b) = " << *it << std::endl;
            }
        }
        out << std::endl;
    }
    std::cout << out.str() << std::endl;
}

template<unsigned long N, unsigned long M, typename Stride>
struct detail {
    static void
    drtileImpl(const vigra::MultiArrayView<M, weight_t, Stride>& A,
               unsigned long w,
               std::vector< vigra::TinyVector<coordinate_t, 3> > & t,
               vigra::TinyVector<coordinate_t, N>& currentShape
              ) {
        #ifdef DEBUG_PRINTING
        std::cout << "detail<"<<N<<","<<M<<">::drtileImpl(A,w="<<w<<") " << std::endl;
        std::cout << "    A =" << std::endl;
        printArray(A, std::string("    "));
        std::cout << "    A.shape =" << A.shape() << std::endl;
        std::cout << "    w       =" << w << std::endl;
        #endif
        
        typedef vigra::TinyVector<coordinate_t, 3> t_t;
        
        //create Abar
        typename if_<M-1==0, vigra::TinyVector<coordinate_t, 1>, vigra::TinyVector<coordinate_t, M-1> >::result Abar_shape;
        if(M-1>=1) {
            for(unsigned long i=0; i<M-1; ++i)
                Abar_shape[i] = A.shape(i);
        }
        else {
            Abar_shape[0] = 1;
        }
        //typename if_<M-1==0, vigra::MultiArray<0, weight_t>, vigra::MultiArray<M-1, weight_t> >::result Abar(Abar_shape);
        vigra::MultiArray<M-1, weight_t> Abar(Abar_shape);
        
        const unsigned long d  = M;
        const unsigned long nd = A.shape(d-1);
        
        coordinate_t prev_k = 0;
        while(prev_k != nd) {
            for(coordinate_t k=prev_k; k<nd+1; ++k) {
                #ifdef DEBUG_PRINTING
                std::cout << "      * prev_k=" << prev_k << ", k=" << k << std::endl;
                #endif
                
                //extend Abar
                if(k<=A.shape(d-1)-1) {
                    if(d-1 == 0) {
                        Abar[0] += A[k];
                    }
                    else {
                        Abar += A.template bind<d-1>(k);
                    }
                }
                
                currentShape[d-1] = k-prev_k;
                
                #ifdef DEBUG_PRINTING
                std::cout << "       * Abar [extend] =" << std::endl;
                printArray(Abar, std::string("        "));
                #endif
                
                //find maximum
                weight_t max = std::numeric_limits<weight_t>::min();
                for(size_t i=0; i<Abar.size(); ++i) {
                    if(Abar[i] > max) {max = Abar[i]; }
                }
                #ifdef DEBUG_PRINTING
                std::cout << "       * max=" << (int)max << std::endl;
                #endif
                
                if(k==nd || max > w) {
                    //unextend Abar
                    if(k<=A.shape(d-1)-1) {
                        if(d-1 == 0) {
                            Abar[0] -= A[k];
                        }
                        else {
                            Abar -= A.template bind<d-1>(k);
                        }
                    }
                    #ifdef DEBUG_PRINTING
                    std::cout << "       * Abar [unextend] =" << std::endl;
                    printArray(Abar, std::string("        "));
                    std::cout << "PUSH: " << d << " " << prev_k << " " << k << std::endl;
                    #endif
                    
                    if(d!=1) {
                        t.push_back(t_t(d, prev_k, k));
                    }
                    else {
                        unsigned long p = 1;
                        for(unsigned long l=0; l<currentShape.size(); ++l) p *= currentShape[l];
                        
                        if (!(p == 1 && Abar[0] ==w)) {
                            t.push_back(t_t(d, prev_k, k));
                        }
                    }
                    
                    if(d>1) {
                        #ifdef DEBUG_PRINTING
                        std::cout << "RECURSE" << std::endl;
                        #endif
                        detail<N,M-1,vigra::StridedArrayTag>::drtileImpl(Abar, w, t, currentShape);
                    }
                    
                    Abar.init(0);
                    prev_k = k;
                    #ifdef DEBUG_PRINTING
                    std::cout << "       * Abar [cleared] =" << std::endl;
                    printArray(Abar, std::string("        "));
                    std::cout << "       * prev_k=" << prev_k << std::endl;
                    #endif
                    break;
                }
            }
        }
    }
};

template<unsigned long N, typename Stride>
struct detail<N,0,Stride> {
    static void
    drtileImpl(const vigra::MultiArrayView<0, weight_t, Stride>& A,
               unsigned long w,
               std::vector< vigra::TinyVector<coordinate_t, 3> > & t,
               vigra::TinyVector<coordinate_t, N>& currentShape
              ) {
    }
};

template<unsigned long N, typename Stride>
vigra::MultiArray<2, coordinate_t>
drtile(const vigra::MultiArrayView<N, weight_t, Stride>& A,
       unsigned long w) {
    #ifdef DEBUG_PRINTING
    std::cout << "drtile(A,w)" << std::endl;
    std::cout << "    A =" << std::endl;
    printArray(A, std::string("    "));
    std::cout << "    A.shape =" << A.shape() << std::endl;
    std::cout << "    w       =" << w << std::endl;
    #endif
    
    std::vector< vigra::TinyVector<coordinate_t, 3> > t;
    vigra::TinyVector<coordinate_t, N> currentCoordinate;
	::detail<N,N,Stride>::drtileImpl(A,w,t, currentCoordinate);
    
    #ifdef DEBUG_PRINTING
    std::cout << "drtile returned:" << std::endl;
    for(unsigned long i=0; i<t.size(); ++i) {
        const coordinate_t& d = t[i][0];
        const coordinate_t& s = t[i][1];
        const coordinate_t& e = t[i][2];
        std::cout << "dimension " << d << ": [" << s << "," << e << ")" << std::endl;
    }
    #endif
    
    typedef vigra::TinyVector<coordinate_t, 2*N> bbox_t;
    typedef vigra::MultiArray<2, coordinate_t> bbox_vector_t;
    
    unsigned long bboxCount = 0;
    for(unsigned long i=0; i<t.size(); ++i) {
        const coordinate_t& d = t[i][0];
        if(d==1) { // || (i < t.size()-1 && d<t[i+1][0])) {
            ++bboxCount;
        }
    }
    
    bbox_vector_t bb(typename bbox_vector_t::size_type(bboxCount, 2*N));
    
    bbox_t b;
    unsigned long j = 0;
    for(unsigned long i=0; i<t.size(); ++i) {
        const coordinate_t& d = t[i][0];
        const coordinate_t& s = t[i][1];
        const coordinate_t& e = t[i][2];
        b[d-1]   = s;
        b[N+d-1] = e;
        if(d==1) { // || (i < t.size()-1 && d<t[i+1][0])) {
            for(unsigned long k=0; k<2*N; ++k) {
                bb(j,k) = b[k];
            }
            ++j;
        }
    }
    return bb;
}

std::string printBbox(vigra::NumpyArray<2, coordinate_t> bb) {
    unsigned long N = bb.shape()[1]/2;
    unsigned long nBboxes = bb.shape()[0];
    
    std::stringstream ss;
    ss << "drtile returned " << nBboxes << " bounding boxes" << std::endl;
    for(unsigned long k=0; k<nBboxes; ++k) {
        ss << "(";
        for(unsigned long i=0; i<N; ++i) {
            ss << bb(k,i);
            if(i!=N-1) ss << ",";
        }
        ss << "), (";
        for(unsigned long i=0; i<N; ++i) {
            ss << bb(k,N+i);
            if(i!=N-1) ss << ",";
        }
        ss << ")" << std::endl;
    }
    return ss.str();
}

using namespace boost::python;
using namespace vigra;

template<unsigned long N>
vigra::MultiArray<2, coordinate_t> test_DRTILE_Impl(const vigra::MultiArrayView<N, weight_t, vigra::StridedArrayTag>& A, weight_t w) {
    vigra::MultiArray<2, coordinate_t> bb = drtile<N, vigra::StridedArrayTag>(A, w);
    //return printBbox<N>(bb);
    return bb;
}

NumpyAnyArray test_DRTILE(NumpyAnyArray A, weight_t w, vigra::NumpyArray<2, coordinate_t> out) {
    if(A.ndim() == 1) {
        vigra::MultiArray<2, coordinate_t> x = test_DRTILE_Impl<1>(NumpyArray<1, weight_t>(A, true), w);
        out.reshapeIfEmpty(x.shape());
        out.copy( x );
    }
    if(A.ndim() == 2) {
        vigra::MultiArray<2, coordinate_t> x = test_DRTILE_Impl<2>(NumpyArray<2, weight_t>(A, true), w);
        out.reshapeIfEmpty(x.shape());
        out.copy( x );
    }
    if(A.ndim() == 3) {
        vigra::MultiArray<2, coordinate_t> x = test_DRTILE_Impl<3>(NumpyArray<3, weight_t>(A, true), w);
        out.reshapeIfEmpty(x.shape());
        out.copy( x );
    }
    if(A.ndim() == 4) {
        vigra::MultiArray<2, coordinate_t> x = test_DRTILE_Impl<4>(NumpyArray<4, weight_t>(A, true), w);
        out.reshapeIfEmpty(x.shape());
        out.copy( x );
    }
    if(A.ndim() == 5) {
        vigra::MultiArray<2, coordinate_t> x = test_DRTILE_Impl<5>(NumpyArray<5, weight_t>(A, true), w);
        out.reshapeIfEmpty(x.shape());
        out.copy( x );
    }
    if(A.ndim() == 6) {
        vigra::MultiArray<2, coordinate_t> x = test_DRTILE_Impl<6>(NumpyArray<6, weight_t>(A, true), w);
        out.reshapeIfEmpty(x.shape());
        out.copy( x );
    }
    return out;
}

std::string test_printBbox(NumpyAnyArray bb) {
    return printBbox(NumpyArray<2, coordinate_t>(bb, true));
}


BOOST_PYTHON_MODULE_INIT(drtile) {
    import_vigranumpy();
    def("test_DRTILE", 
        registerConverters(&test_DRTILE),
        (
            arg("A"), arg("w"), arg("out") = object()
        ),
        "DRTILE"
    );
    def("test_printBbox", 
        registerConverters(&test_printBbox),
        (
            arg("bb")
        ),
        "printBbox"
    );
}


// unsigned long main() {
//     const unsigned long N=2;
//     typedef vigra::MultiArray<N, weight_t> array_t;
//     typedef std::vector< vigra::TinyVector<coordinate_t, 2*N> > bbox_vector_t;
//     
//     array_t A(array_t::size_type(8,5));
//     
//     A(0,0) = 1;  A(0,1) = 1;  A(0,2) = 1;  A(0,3) = 1;  A(0,4) = 1;  A(1,0) = 1;  A(1,1) = 0;  A(1,2) = 0;  A(1,3) = 1;  A(1,4) = 1;  A(2,0) = 1;  A(2,1) = 1;  A(2,2) = 0;  A(2,3) = 1;  A(2,4) = 1;  A(3,0) = 1;  A(3,1) = 1;  A(3,2) = 0;  A(3,3) = 0;  A(3,4) = 1;  A(4,0) = 1;  A(4,1) = 1;  A(4,2) = 0;  A(4,3) = 0;  A(4,4) = 1;  A(5,0) = 1;  A(5,1) = 1;  A(5,2) = 1;  A(5,3) = 1;  A(5,4) = 1;  A(6,0) = 1;  A(6,1) = 1;  A(6,2) = 1;  A(6,3) = 0;  A(6,4) = 0;  A(7,0) = 1;  A(7,1) = 1;  A(7,2) = 1;  A(7,3) = 0;  A(7,4) = 0;
//     
//     bbox_vector_t bb = drtile<N>(A, 1);
//     printBbox<N>(bb);
// }
//     
