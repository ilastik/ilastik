//#include <Python.h>
#include <iostream>
#include <boost/python.hpp>
#include <set>

#include <vigra/numpy_array.hxx>
#include <vigra/numpy_array_converters.hxx>
#include <vigra/multi_convolution.hxx>
#include <vigra/functorexpression.hxx>

#include "starContext.hxx"
#include "starContextMulti.hxx"
#include "histogram.hxx"

namespace python = boost::python;

namespace vigra
{
template <class T>
NumpyAnyArray pythonSimpleContext(NumpyArray<2, Singleband<T> > predictions, NumpyArray<2, Singleband<T> > res = python::object())
{

	res.reshapeIfEmpty(predictions.shape(), "simpleContext(): Output array has wrong shape.");
    std::cout<<"res.shape: "<<res.shape()[0]<<std::endl;
    int count = 0;
    for (int iobs=0; iobs<predictions.shape()[0]; iobs++){
        for (int ilabel=0; ilabel<predictions.shape()[1]; ilabel++){
            res[count]=predictions[count];
            count++;
        }
    }
	}

    return res;
}

template <class IND, class T>
NumpyAnyArray pythonStarContext3D(NumpyArray<1, Singleband<IND> > radii, 
                                  NumpyArray<1, Singleband<IND> > fullshape,
                                  NumpyArray<1, Singleband<IND> > selections,
                                  NumpyArray<2, Singleband<T> > predictions, 
                                  NumpyArray<2, Singleband<T> > res = python::object())

{
	{ PyAllowThreads _pythread;
    //std::cout<<"full shape: "<<fullshape[0]<<" "<<fullshape[1]<<" "<<fullshape[2]<<std::endl;
    //std::cout<<"shape shape: "<<fullshape.size()<<std::endl;
    //std::cout<<"predictions: "<<predictions.shape()<<std::endl;
    
    starContext3D(radii, fullshape, selections, predictions, res);
   
    std::cout<<"back at glue function"<<std::endl;
    std::cout<<"res shape: "<<res.shape()<<std::endl;
	}
    return res;
}

template <class IND, class T>
NumpyAnyArray pythonStarContext2D(NumpyArray<1, Singleband<IND> > radii, 
                                  NumpyArray<1, Singleband<IND> > fullshape,
                                  NumpyArray<1, Singleband<IND> > selections,
                                  NumpyArray<2, Singleband<T> > predictions, 
                                  NumpyArray<2, Singleband<T> > res = python::object())
{
	{ PyAllowThreads _pythread;

	starContext2D(radii, fullshape, selections, predictions, res);
    std::cout<<"returning results: "<<res.shape()<<std::endl;
    return res;

	}
}

template <class IND, class T>
NumpyAnyArray pythonStarContext2Dmulti(NumpyArray<1, Singleband<IND> > radii,
                                  NumpyArray<3, Multiband<T> > predictions,
                                  NumpyArray<3, Multiband<T> > res = python::object())
{
	{ PyAllowThreads _pythread;
	starContext2Dmulti(radii, predictions, res);
    std::cout<<"back at glue function"<<std::endl;
	}

    return res;

}
                   
template <class T1, class T2>
NumpyAnyArray
pythonHistogram2D(NumpyArray<3, Multiband<T1> > predictions,
				  int nbins=4,
                  NumpyArray<3, Multiband<T2> > res=python::object())
{
	{ PyAllowThreads _pythread;


	int h=predictions.shape(0);
	int w=predictions.shape(1);
	int c=predictions.shape(2);

	vigra_precondition(c>=2,"right now is better");

	MultiArrayShape<3>::type sh(h,w,c);
    res.reshapeIfEmpty(sh);

    histogram2D(predictions,nbins,res);

	}
    return res;


}

template <class T1, class T2>
NumpyAnyArray
pythonIntegralHistogram2D(NumpyArray<3, Multiband<T1> > predictions,
				  int nbins=4,
                  NumpyArray<3, Multiband<T2> > res=python::object())
{

	{ PyAllowThreads _pythread;


	int h=predictions.shape(0);
	int w=predictions.shape(1);
	int nc=predictions.shape(2);

	vigra_precondition(nc>=2,"right now is better");

	MultiArrayShape<3>::type sh(h,w,c);
    res.reshapeIfEmpty(sh);

    integralHistogram2D(predictions,nbins,res);

	}

    return res;

}

                   
void defineContext() {
    using namespace python;
    //def("simpleContext", registerConverters(&pythonSimpleContext<float>), (arg("predictions"), arg("out")=python::object()));
    def("starContext3D", registerConverters(&pythonStarContext3D<int, float>), (arg("radii"), arg("fullshape"), arg("selections"), 
                                                                            arg("predictions"), arg("out")=python::object()));
    def("starContext3D", registerConverters(&pythonStarContext3D<unsigned int, float>), (arg("radii"), arg("fullshape"), arg("selections"), 
                                                                            arg("predictions"), arg("out")=python::object()));  
    def("starContext2D", registerConverters(&pythonStarContext2D<int, float>), (arg("radii"), arg("fullshape"), arg("selections"), 
                                                                            arg("predictions"), arg("out")=python::object()));
    def("starContext2D", registerConverters(&pythonStarContext2D<unsigned int, float>), (arg("radii"), arg("fullshape"), arg("selections"), 
                                                                            arg("predictions"), arg("out")=python::object()));                                                                         
    def("starContext2Dmulti", registerConverters(&pythonStarContext2Dmulti<unsigned int, float>), (arg("radii"), arg("predictions"),
																			arg("out")=python::object()));

    def("starContext2Dmulti",registerConverters(&pythonStarContext2Dmulti<int, float>) , (arg("radii"), arg("predictions"),
        		arg("out")=python::object()));


    //histograms features
    def("histogram2D",registerConverters(&pythonHistogram2D<float, float>) , (arg("predictions"), arg("nbin")=4,
                                                                                             arg("out")=python::object()));
    def("intHistogram2D",registerCondajklasjverters(&pythonIntegralHistogram2D<float, float>) , (arg("predictions"), arg("nbin")=4,
                                                                                                arg("out")=python::object()));
}


using namespace vigra;
using namespace boost::python;

BOOST_PYTHON_MODULE_INIT(context)
{
    import_vigranumpy();
    defineContext();
}
