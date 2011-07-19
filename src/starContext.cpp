#include <iostream>
#include <vector>

#include <vigra/multi_array.hxx>
#include <vigra/numpy_array.hxx>
#include <vigra/numpy_array_converters.hxx>
#include <vigra/multi_pointoperators.hxx>

template <class SrcIterator, class SrcAccessor,class SrcShape,
          class DestIterator, class DestAccessor>
int simpleContext(SrcIterator s_Iter, SrcShape srcShape, SrcAccessor sa,
                         DestIterator d_Iter, DestAccessor da)
{
    // for the moment, just copy the predictions to features
    int nobs = srcShape[0], nlabels = srcShape[1];
   
    int iobs, ilabel, ifeature;       
    
    DestIterator ds = d_Iter;
    SrcIterator ss = s_Iter;
    
    for (iobs=0; iobs<nobs; ++iobs, ++ss.dim<1>(), ++ds.dim<1>()) {
        ifeature=0;
        for (ilabel=0; ilabel<nlabels; ++ilabel, ++ss.dim<0>) {
            pred = sa(ss);
            ds.dim<0>() += ifeature;
            da(ds) = pred;
            ifeature++;
        }
    }
    return 1;
}
           
                
    
