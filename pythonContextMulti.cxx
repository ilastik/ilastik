#include <Python.h>
#include <iostream>
#include <boost/python.hpp>
#include <set>

#include <vigra/numpy_array.hxx>
#include <vigra/numpy_array_converters.hxx>
#include <vigra/multi_convolution.hxx>
#include <vigra/functorexpression.hxx>

#include "starContext.hxx"
#include "starContextMulti.hxx"


namespace python = boost::python;

namespace vigra
{
template <class IND, class T>
NumpyAnyArray pythonStarContext2Dmulti(NumpyArray<1, Singleband<IND> > radii,
                                       NumpyArray<3, Multiband<T> > predictions,
                                       NumpyArray<3, Multiband<T> > res = python::object())
{
    
    starContext2Dmulti(radii, predictions, res);
    std::cout<<"back at glue function"<<std::endl;
    return res;
}

template <class IND, class T>
NumpyAnyArray pythonAvContext2Dmulti(NumpyArray<1, Singleband<IND> >& sizes,
                                     NumpyArray<3, Multiband<T> >& predictions,
                                     NumpyArray<3, Multiband<T> >& res)
{
    avContext2Dmulti(sizes, predictions, res);
    std::cout<<"back at glue function"<<std::endl;
    return res;
}

void defineContext() {
    using namespace python;
                                                                        
    def("starContext2Dmulti", registerConverters(&pythonStarContext2Dmulti<unsigned int, float>), (arg("radii"), arg("predictions"),
                                                                                         arg("out")=python::object()));
    def("starContext2Dmulti", registerConverters(&pythonStarContext2Dmulti<int, float>), (arg("radii"), arg("predictions"),
                                                                                         arg("out")=python::object()));                                                                                         
    def("avContext2Dmulti", registerConverters(&pythonAvContext2Dmulti<int, float>), (arg("sizes"), arg("predictions"),
                                                                                      arg("out")=python::object()));
    def("avContext2Dmulti", registerConverters(&pythonAvContext2Dmulti<unsigned int, float>), (arg("sizes"), arg("predictions"),
                                                                                      arg("out")=python::object()));                                                                                   
}
} //namespace vigra

using namespace vigra;
using namespace boost::python;

BOOST_PYTHON_MODULE_INIT(context)
{
    import_vigranumpy();
    defineContext();
}