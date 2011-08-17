#ifndef HISTOGRAM_HXX
#define HISTOGRAM_HXX

#include <vigra/multi_array.hxx>
#include <vigra/multi_pointoperators.hxx>
#include <vigra/utilities.hxx>
#include <iostream>
#include <cmath>
using namespace vigra;

template<class T1,class T2>
int getIndex(T1& value, int nbins, T2 min, T2 max) {

	if (value==1)
		return nbins-1;

	int index;
	double dt = double(max-min) / double(nbins);

	index = std::ceil(double(value) / dt)-1;
	if (value==min)
		++index;
	return index;
}

template<class T>
int getIndex(const T& value, int nbins) {

	if (value==1)
		return nbins-1;

	int res;
	double dt = 1.0 / double(nbins);

	//if (value == 1)
	//	nbins -= 1;

	res = value / dt;
	if (res >= nbins)
		throw std::runtime_error(
			"Not implementex for stuff otside ot the interval [0,1]");

	return res;
}


//compute the pixel histogram of a given image
//for multichannel images, compute channelwise
// The imput shoudl be a multiarray view last index indicating the channel
// The result is a Histogram where last index loops through the bins
// NB Assumes that the values of each channel in the original image are between 0,1
template<class T, class T2, class S1, class S2>
void histogram2D(const MultiArrayView<3, T, S1>& image, int nbins,
		MultiArrayView<3, T2, S2>& Hist) {

	int width = image.shape()[0];
	int height = image.shape()[1];
	int nc = image.shape()[2];

	MultiArrayShape<3>::type resShp(width, height, nc * nbins);
	vigra_precondition(resShp[2]==Hist.shape(2),"wrong shape");

	MultiArrayShape<3>::type p(0, 0, 0);

	int x,y,c,index;

	for (c = 0; c < nc; c++) {
		for (y = 0; y < height; y++) {
			for (x = 0; x < width; x++) {

				T value=image(x,y,c);

				if (value<0 | value>1)
					throw std::runtime_error("allowed only values between 0 and 1");

				index = getIndex(value, nbins,0,1);

				index = index + nbins * c;

				Hist(x, y, index)+=1;

			}

		}

	}

}

//compute the pixel histogram of a given image
//for multichannel images, compute channelwise
// we can choose an amount of overlap beteeen different pixels
// The imput shoudl be a multiarray view last index indicating the channel
// The result is a Histogram where last index loops through the bins
// NB Assumes that the values of each channel in the original image are between 0,1
template<class T, class S1, class S2>
void overlappingHistogram2D(MultiArrayView<3, T, S1>& image, int nbins,
		float frac_overlap, MultiArrayView<3, float, S2>& Hist) {

	vigra_precondition(frac_overlap>=0 && frac_overlap<1,"fractionary overlap between [0,1)");

	int width = image.shape()[0];
	int height = image.shape()[1];
	int nc = image.shape()[2];

	MultiArrayShape<3>::type resShp(width, height, nc * nbins);
	vigra_precondition(resShp[2]==Hist.shape(2),"wrong shape");

	int x, y, c, index;

	double dt = 1 / double(nbins);
	double ddt = dt * frac_overlap;

	//Do this for all the channels
	for (c = 0; c < nc; c++) {

		int shift=nbins*c; //shift to write the result to corret bin

		for (y = 0; y < height; y++)
		{
			for (x = 0; x < width; x++)
			{
				double t = 0;

				T val = image(x, y, c);
				if (val <= dt + 2 * ddt)
					++Hist(x, y, shift+0);
				t += dt;

				for (int k = 1; k < nbins - 1; k++)
				{
					if (val > t - ddt && val <= t + dt + ddt)
						++Hist(x, y, shift + k);
					t += dt;
				}

				if (nbins - 2 >= 0)
					if (val <= 1 && val > 1 - dt - 2 * ddt)
						++Hist(x, y, shift + (nbins - 1));

			}
		}
	}

}

//compute integral histogram of a given image
//for multichannel images, compute channelwise
// we can choose an amount of overlap beteeen different pixels
// The imput shoudl be a multiarray view last index indicating the channel
// The result is a Histogram where last index loops through the bins
// NB Assumes that the values of each channel in the original image are between 0,1
template<class T1,class T2, class S1, class S2>
void
integralHistogram2D(MultiArrayView<3, T1, S1>& image, int nbins,
		MultiArrayView<3, T2, S2>& H) {

	//FIXME you are imposing between zero and 1
	int height = image.shape()[0];
	int width = image.shape()[1];
	int nc = image.shape()[2];
	int x,y,c,index;
	MultiArrayShape<3>::type resShp(width, height, nc * nbins);
	vigra_precondition(resShp[2]==H.shape(2),"wrong shape");




	std::cerr << "inside c++" << std::endl;
	//For all the channels do the same
	for (c=0;c<nc;c++)
	{
		int shift=c*nbins;
		//std::cerr << "here" << std::endl ;

		//initialize the histogram
		for(int j=shift; j<nbins+shift;j++)
		{
			H(0,0,j)=0;
		}

		index=getIndex(image(0,0,c),nbins,0,1)+shift;
		H(0,0,index)+=1;

		for (y=1;y<height;y++)
		{
			index=getIndex(image(y,0,c),nbins,0,1)+shift;

			for(int j=shift; j<nbins+shift;j++)
			{
				H(y,0,j)=H(y-1,0,j);
			}
			H(y,0,index)+=1;
		}

		for (x=1;x<width;x++)
		{
			index=getIndex(image(0,x,c),nbins,0,1)+shift;
			for(int j=shift; j<nbins+shift;j++)
			{
				H(0,x,j)=H(0,x-1,j);
			}
			H(0,x,index)+=1;
		}

		for (y=1;y<height;y++)
			for(x=1;x<width;x++)
			{
				index=getIndex(image(y,x,c),nbins,0,1)+shift;
				for(int j=shift; j<nbins+shift;j++)
				{
					H(y,x,j)=H(y,x-1,j)+H(y-1,x,j)-H(y-1,x-1,j);
				}
				H(y,x,index)+=1;

			}

		}

}





#endif
