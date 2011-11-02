#define PY_ARRAY_UNIQUE_SYMBOL context_multi_PyArray_API

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
#include "contextAverage.hxx"
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
NumpyAnyArray pythonStarContext3Dvar(NumpyArray<1, Singleband<IND> > radii_x,
                            NumpyArray<1, Singleband<IND> > radii_y,
                            NumpyArray<1, Singleband<IND> > radii_z,
                            NumpyArray<4, Multiband<T> > predictions,
                            NumpyArray<4, Multiband<T> > res)
{
    {PyAllowThreads _pythread;
    std::cout<<"calling function"<<std::endl;
    std::cout<<"shapes: "<<radii_x.shape()<<" "<<radii_y.shape()<<" "<<radii_z.shape()<<" "<<predictions.shape()<<std::endl;
    starContext3Dvar(radii_x, radii_y, radii_z, predictions, res);
    }
    return res;
}

template <class IND, class T>
NumpyAnyArray pythonStarContext3Dnew(NumpyArray<2, Singleband<IND> > radii_triplets,
                                        NumpyArray<4, Multiband<T> > predictions,
                                        NumpyArray<4, Multiband<T> > res)
{
    { PyAllowThreads _pythread;
    starContext3Dnew(radii_triplets, predictions, res);
    std::cout<<"c++ done"<<std::endl;
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
//     std::cout<<"back at glue function"<<std::endl;
	}
    return res;
}

template <class IND, class T>
NumpyAnyArray pythonVarContext2Dmulti(NumpyArray<1, Singleband<IND> > sizes,
                             NumpyArray<3, Multiband<T> > predictions,
                             NumpyArray<3, Multiband<T> > res)
{
    { PyAllowThreads _pythread;
    varContext2Dmulti(sizes, predictions, res);
//     std::cout<<"back at glue function"<<std::endl;
    }
    return res;
}

template <class IND, class T>
NumpyAnyArray pythonVarContext3Dmulti(NumpyArray<1, Singleband<IND> > sizes,
                             NumpyArray<4, Multiband<T> > predictions,
                             NumpyArray<4, Multiband<T> > res)
{
    { PyAllowThreads _pythread;
    varContext3Dmulti(sizes, predictions, res);
//     std::cout<<"back at glue function"<<std::endl;
    }
    return res;
}



template <class T>
NumpyAnyArray pythonIntegralImage(NumpyArray<3, Multiband<T> > image,
                                  NumpyArray<3, Multiband<T> > res)
{
	{ PyAllowThreads _pythread;
    integralImage(image, res);
//     std::cout<<"back at glue function"<<std::endl;
	}
    return res;
}


template <class T>
NumpyAnyArray pythonIntegralImage2(NumpyArray<3, Multiband<T> > image,
                                  NumpyArray<3, Multiband<T> > res)
{   
    { PyAllowThreads _pythread;
    integralImage2(image, res);
    }
//     std::cout<<"back at glue function"<<std::endl;
    return res;
}

template <class T>
NumpyAnyArray pythonIntegralVolume(NumpyArray<4, Multiband<T> > volume,
                                   NumpyArray<4, Multiband<T> > res)
{   
    { PyAllowThreads _pythread;
    integralVolume(volume, res);
    }
    return res;
}

/****************************************************************************/

//Begin histogram wrapping
template <class T1, class T2>
NumpyAnyArray
pythonHistogram2D(NumpyArray<3, Multiband<T1> > predictions,
				  int nbins=4)
                  //NumpyArray<3, Multiband<T2> > res=python::object())
{


	int h=predictions.shape(0);
	int w=predictions.shape(1);
	int c=predictions.shape(2);

	//vigra_precondition(c>=2,"right now is better");
	MultiArrayShape<3>::type sh(h,w,c*nbins);
	NumpyArray<3, T2 >res(sh);

	{
	    	PyAllowThreads _pythread;

	    	histogram2D(predictions,nbins,res);

	}

    return res;


}


template <class T1, class T2 >
NumpyAnyArray
pythonOverlappingHistogram2D(NumpyArray<3, Multiband<T1> > predictions,
				  int nbins=4, float frac_overlap=0.33)
                  //NumpyArray<3, Multiband<float> > res=python::object())
{


	int h=predictions.shape(0);
	int w=predictions.shape(1);
	int c=predictions.shape(2);

	vigra_precondition(c>=2,"right now is better");
	MultiArrayShape<3>::type sh(h,w,c*nbins);
	NumpyArray<3, T2 >res(sh);

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


	{
		PyAllowThreads _pythread;
		integralHistogram2D(predictions,nbins,res);

	}

    return res;

}

template <class T1, class T2>
NumpyAnyArray
pythonIntegralOverlappingHistogram2D(NumpyArray<3, Multiband<T1> > predictions,
                                  int nbins=5, double frac_overlap=0.2)
                  //NumpyArray<3, Multiband<T2> > res=python::object())
{
	int h=predictions.shape(0);
	int w=predictions.shape(1);
	int nc=predictions.shape(2);

	MultiArrayShape<3>::type sh(h,w,nc*nbins);
	//res.reshapeIfEmpty(sh);
	NumpyArray<3,T2> res(sh);


	{
		PyAllowThreads _pythread;
		integralOverlappingHistogram2D(predictions,nbins,frac_overlap,res);

	}

    return res;

}

template <class T1, class T2>
NumpyAnyArray
pythonIntegralOverlappingWeightLinHistogram2D(NumpyArray<3, Multiband<T1> > predictions,
                                  int nbins=5, double frac_overlap=0.2)
                  //NumpyArray<3, Multiband<T2> > res=python::object())
{
	int h=predictions.shape(0);
	int w=predictions.shape(1);
	int nc=predictions.shape(2);

	MultiArrayShape<3>::type sh(h,w,nc*nbins);
	//res.reshapeIfEmpty(sh);
	NumpyArray<3,T2> res(sh);


	{
		PyAllowThreads _pythread;
                integralOverlappingWeightLinHistogram2D(predictions,nbins,frac_overlap,res);

	}

    return res;

}

template <class T1, class T2>
NumpyAnyArray
pythonIntegralOverlappingWeightGaussHistogram2D(NumpyArray<3, Multiband<T1> > predictions,
                                  int nbins=5, double sigma=0.5)
                  //NumpyArray<3, Multiband<T2> > res=python::object())
{
        int h=predictions.shape(0);
        int w=predictions.shape(1);
        int nc=predictions.shape(2);

        MultiArrayShape<3>::type sh(h,w,nc*nbins);
        //res.reshapeIfEmpty(sh);
        NumpyArray<3,T2> res(sh);


        {
                PyAllowThreads _pythread;
                integralOverlappingWeightGaussHistogram2D(predictions,nbins,sigma,res);

        }

    return res;

}


template <class T1, class T2 >
NumpyAnyArray
pythonOverlappingWeightLinHistogram2D(NumpyArray<3, Multiband<T1> > predictions,
                                  int nbins=5, double frac_overlap=0.2)
                  //NumpyArray<3, Multiband<float> > res=python::object())
{


        int h=predictions.shape(0);
        int w=predictions.shape(1);
        int c=predictions.shape(2);

        vigra_precondition(c>=2,"right now is better");
        MultiArrayShape<3>::type sh(h,w,c*nbins);
        NumpyArray<3, T2 >res(sh);

        {
                PyAllowThreads _pythread;

                overlappingWeightLinHistogram2D(predictions,nbins,frac_overlap,res);

        }

    return res;


}



template <class T1, class T2 >
NumpyAnyArray
pythonOverlappingWeightGaussHistogram2D(NumpyArray<3, Multiband<T1> > predictions,
                                  int nbins=5, double sigma=0.5)
                  //NumpyArray<3, Multiband<float> > res=python::object())
{


        int h=predictions.shape(0);
        int w=predictions.shape(1);
        int c=predictions.shape(2);

        vigra_precondition(c>=2,"right now is better");
        MultiArrayShape<3>::type sh(h,w,c*nbins);
        NumpyArray<3, T2 >res(sh);

        {
                PyAllowThreads _pythread;

                overlappingWeightGaussHistogram2D(predictions,nbins,sigma,res);

        }

    return res;


}


template <class IND, class T>
NumpyAnyArray pythonContextHistogram2D(NumpyArray<1, Singleband<IND> > radii, int nbins,
                                       NumpyArray<3, Multiband<T> > predictions,
                                       NumpyArray<3, Multiband<T> > res)
{
    //assume that the result array is allocated outside
    
    {
        PyAllowThreads _pythread;
        contextHistogram2D(radii, nbins, predictions, res);
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
    def("varContext2Dmulti", registerConverters(&pythonVarContext2Dmulti<int, float>), (arg("sizes"), arg("predictions"),
                                                                                      arg("out")=python::object()));
    def("varContext2Dmulti", registerConverters(&pythonVarContext2Dmulti<unsigned int, float>), (arg("sizes"), arg("predictions"),
                                                                                      arg("out")=python::object())); 
    def("varContext3Dmulti", registerConverters(&pythonVarContext3Dmulti<unsigned int, float>), (arg("sizes"), arg("predictions"),
                                                                                      arg("out")=python::object())); 

    def("starContext3Dvar", registerConverters(&pythonStarContext3Dvar<int, float>), (arg("radii_x"), arg("radii_y"), arg("radii_z"),
                                                                                      arg("predictions"), arg("out")=python::object()));
    def("starContext3Dvar", registerConverters(&pythonStarContext3Dvar<unsigned int, float>), (arg("radii_x"), arg("radii_y"), arg("radii_z"),
                                                                                      arg("predictions"), arg("out")=python::object()));
    def("starContext3Dnew", registerConverters(&pythonStarContext3Dnew<int, float>), (arg("radii_triplets"), arg("predictions"),
                                                                                      arg("out")=python::object()));
    def("starContext3Dnew", registerConverters(&pythonStarContext3Dnew<unsigned int, float>), (arg("radii_triplets"), arg("predictions"),
                                                                                      arg("out")=python::object()));                                                                                  
                                                                                      
                                                                                      //we define for floats because we want to use it on probability maps                                                                                  
    def("integralImage", registerConverters(&pythonIntegralImage<float>), (arg("image"), arg("out")=python::object()));
    def("integralImage2", registerConverters(&pythonIntegralImage2<float>), (arg("image"), arg("out")=python::object()));
    def("integralVolume", registerConverters(&pythonIntegralVolume<float>), (arg("volume"), arg("out")=python::object()));
    
    /*************************************************************************************************************************/
    // Start histogram
    def("histogram2D",registerConverters(&pythonHistogram2D<float, float>) , (arg("predictions"), arg("nbin")=4));
																				//arg("out")=python::object()));

    def("overlappingHistogram2D",registerConverters(&pythonOverlappingHistogram2D<float,float>) , (arg("predictions"), arg("nbin")=4, arg("f_overlap")=0.33));
    																				//arg("out")=python::object()));


    def("intHistogram2D",registerConverters(&pythonIntegralHistogram2D<float, float>) , (arg("predictions"), arg("nbin")=4));
    def("intHistogram2D",registerConverters(&pythonIntegralHistogram2D<double, double>) , (arg("predictions"), arg("nbin")=4));

    def("intOverlappingHistogram2D",registerConverters(&pythonIntegralOverlappingHistogram2D<float, float>) , (arg("predictions"), arg("nbin")=5, arg("f_overlap")=0.2 ));
    def("intOverlappingHistogram2D",registerConverters(&pythonIntegralOverlappingHistogram2D<double, double>) , (arg("predictions"), arg("nbin")=5, arg("f_overlap")=0.2 ));

    def("intOverlappingWeightLinHistogram2D",registerConverters(&pythonIntegralOverlappingWeightLinHistogram2D<float, float>) , (arg("predictions"), arg("nbin")=5, arg("f_overlap")=0.2 ));
    def("intOverlappingWeightLinHistogram2D",registerConverters(&pythonIntegralOverlappingWeightLinHistogram2D<double, double>) , (arg("predictions"), arg("nbin")=5, arg("f_overlap")=0.2 ));

    def("overlappingWeightLinHistogram2D",registerConverters(&pythonOverlappingWeightLinHistogram2D<float,float>) , (arg("predictions"), arg("nbin")=5, arg("f_overlap")=0.2));
    def("overlappingWeightLinHistogram2D",registerConverters(&pythonOverlappingWeightLinHistogram2D<double,double>) , (arg("predictions"), arg("nbin")=5, arg("f_overlap")=0.2));

    def("intOverlappingWeightGaussHistogram2D",registerConverters(&pythonIntegralOverlappingWeightGaussHistogram2D<float, float>) , (arg("predictions"), arg("nbin")=5, arg("sigma")=0.5 ));
    def("intOverlappingWeightGaussHistogram2D",registerConverters(&pythonIntegralOverlappingWeightGaussHistogram2D<double, double>) , (arg("predictions"), arg("nbin")=5, arg("sigma")=0.5 ));

    def("overlappingWeightGaussHistogram2D",registerConverters(&pythonOverlappingWeightGaussHistogram2D<float,float>) , (arg("predictions"), arg("nbin")=5, arg("sigma")=0.5));
    def("overlappingWeightGaussHistogram2D",registerConverters(&pythonOverlappingWeightGaussHistogram2D<double,double>) , (arg("predictions"), arg("nbin")=5, arg("sigma")=0.5));

                                                                                                    //arg("out")=python::object()));
    def("contextHistogram2D", registerConverters(&pythonContextHistogram2D<int, float>), (arg("radii"), arg("nbins"), arg("predictions"),
                                                                                         arg("out")=python::object()));
    def("contextHistogram2D", registerConverters(&pythonContextHistogram2D<unsigned int, float>), (arg("radii"), arg("nbins"), arg("predictions"),
                                                                                         arg("out")=python::object()));

}
//} //namespace vigra

using namespace vigra;
using namespace boost::python;

BOOST_PYTHON_MODULE_INIT(contextcpp)
{

    import_vigranumpy();
    defineContext();
}
