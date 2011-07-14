#ifndef INTEGRALIMAGE_HXX
#define INTEGRALIMAGE_HXX

#include <vigra/multi_array.hxx>
#include <vigra/numpy_array.hxx>
#include <vigra/numpy_array_converters.hxx>
#include <vigra/multi_pointoperators.hxx>
#include <vigra/utilities.hxx>

using namespace vigra;

template <class T, class S1, class S2>
void integralImage(MultiArrayView<3, T, S1>& image, MultiArrayView<3, T, S2>& intimage)
{
    //compute the integral image of a given image
    //for multichannel images, compute channelwise
    
    int width = image.shape()[0];
    int height = image.shape()[1];
    int nc = image.shape()[2];
    for (int c=0; c<nc; ++c){
        T s = 0;
        for (int i=0; i<width; ++i){
            s += image(0, i, c);
            intimage(0, i, c)=s;
        }
        for (int i=1; i<width; ++i){
            s=0;
            for (int j=0; j<height; ++j){
                s+=image(i, j, c);
                intimage(i, j, c) = s+intimage(i-1, j, c);
            }
        }
    }
    return;
}
#endif