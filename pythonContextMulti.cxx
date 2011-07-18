//#include <Python.h>
#include <iostream>
#include <boost/python.hpp>
#include <set>

#include <vigra/numpy_array.hxx>
#include <vigra/numpy_array_converters.hxx>
#include <vigra/multi_convolution.hxx>
#include <vigra/functorexpression.hxx>

//#include "starContext.hxx"
#include "starContextMulti.hxx"
#include "integralImage.hxx"
#include "histogram.hxx"

namespace python = boost::python;

//namespace vigra
//{
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

template <class IND, class T>
NumpyAnyArray pythonAvContext2Dmulti(NumpyArray<1, Singleband<IND> > sizes,
                                     NumpyArray<3, Multiband<T> > predictions,
                                     NumpyArray<3, Multiband<T> > res)
{
	{ PyAllowThreads _pythread;
    avContext2Dmulti(sizes, predictions, res);
    std::cout<<"back at glue function"<<std::endl;
	}
    return res;
}

template <class T>
NumpyAnyArray pythonIntegralImage(NumpyArray<3, Multiband<T> > image,
                                  NumpyArray<3, Multiband<T> > res)
{
	{ PyAllowThreads _pythread;
    integralImage(image, res);
    std::cout<<"back at glue function"<<std::endl;
	}
    return res;
}

/****************************************************************************/

//Begin histogram wrapping
template <class T1, class T2>
NumpyAnyArray
pythonHistogram2D(NumpyArray<3, Multiband<T1> > predictions,
				  int nbins=4,
                  NumpyArray<3, Multiband<T2> > res=python::object())
{


	int h=predictions.shape(0);
	int w=predictions.shape(1);
	int c=predictions.shape(2);

	vigra_precondition(c>=2,"right now is better");
	MultiArrayShape<3>::type sh(h,w,c*nbins);
	    res.reshapeIfEmpty(sh);

	{
	    	PyAllowThreads _pythread;

	    	histogram2D(predictions,nbins,res);

	}

    return res;


}



template <class T1 >
NumpyAnyArray
pythonOverlappingHistogram2D(NumpyArray<3, Multiband<T1> > predictions,
				  int nbins=4, float frac_overlap=0.33,
                  NumpyArray<3, Multiband<float> > res=python::object())
{


	int h=predictions.shape(0);
	int w=predictions.shape(1);
	int c=predictions.shape(2);

	vigra_precondition(c>=2,"right now is better");
	MultiArrayShape<3>::type sh(h,w,c*nbins);
	    res.reshapeIfEmpty(sh);

	{
	    	PyAllowThreads _pythread;

	    	overlappingHistogram2D(predictions,nbins,frac_overlap,res);

	}

    return res;


}



template <class T1, class T2>
NumpyAnyArray
pythonIntegralHistogram2D(NumpyArray<3, Multiband<T1> > predictions,
				  int nbins=4)
                  //NumpyArray<3, Multiband<T2> > res=python::object())
{
	int h=predictions.shape(0);
	int w=predictions.shape(1);
	int nc=predictions.shape(2);

	MultiArrayShape<3>::type sh(h,w,nc*nbins);
	//res.reshapeIfEmpty(sh);
	NumpyArray<3,T2> res(sh);
	std::cerr << "after";

	{
		PyAllowThreads _pythread;
		integralHistogram2D(predictions,nbins,res);

	}

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
    //we define for floats because we want to use it on probability maps                                                                                  
    def("integralImage", registerConverters(&pythonIntegralImage<float>), (arg("image"), arg("out")=python::object()));

    // Start histogram
    def("histogram2D",registerConverters(&pythonHistogram2D<float, float>) , (arg("predictions"), arg("nbin")=4,
																				arg("out")=python::object()));

    def("histogram2D",registerConverters(&pythonOverlappingHistogram2D<float>) , (arg("predictions"), arg("nbin")=4, arg("f_overlap")=0.33,
    																				arg("out")=python::object()));


    def("intHistogram2D",registerConverters(&pythonIntegralHistogram2D<float, float>) , (arg("predictions"), arg("nbin")=4));
                                                                                                    //arg("out")=python::object()));
}
//} //namespace vigra

using namespace vigra;
using namespace boost::python;

BOOST_PYTHON_MODULE_INIT(context)
{
    import_vigranumpy();
    defineContext();
}
