#ifndef HISTOGRAM_HXX
#define HISTOGRAM_HXX

#include <vigra/multi_array.hxx>
#include <vigra/multi_pointoperators.hxx>
#include <vigra/utilities.hxx>
# include <iostream>
using namespace vigra;

template<class T>
int getIndex(const T& value, int nbins) {

	if (value==1)
		return nbins-1;

	int res;
	double dt = 1.0 / double(nbins);

	std::cerr << value << std::endl;
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

	int index;

	for (p[2] = 0; p[2] < nc; p[2]++) {
		for (p[1] = 0; p[1] < height; p[1]++) {
			for (p[0] = 0; p[0] < width; p[0]++) {
				index = getIndex(image[p], nc);

				index = index + nbins * p[2];

				++Hist(p[0], p[1], index);

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
		double frac_overlap, MultiArrayView<3, double, S2>& Hist) {

	vigra_precondition(frac_overlap>=0 && frac_overlap<1,"fractionary overlap between [0,1)");

	int width = image.shape()[0];
	int height = image.shape()[1];
	int nc = image.shape()[2];

	MultiArrayShape<3>::type shapeHist(width, height, nc * nbins);
	Hist.reshape(shapeHist, 0.0);

	int x, y, c, index;

	double dt = 1 / double(nbins);
	double ddt = dt * frac_overlap;

	for (c = 0; c < nc; c++) {

		for (y = 0; y < height; y++) {
			MultiArrayView<2, T, StridedArrayTag> view1 = Hist.bindAt(1, y);

			for (x = 0; x < width; x++) {
				double t = 0;
				MultiArrayView<1, T, StridedArrayTag> view2 =
						view1.bindAt(0, x); //view though the channels hist at at position x,y

				T val = image(x, y, c);

				if (val <= dt + 2 * ddt)
					++Hist(x, y, nbins * c);
				t += dt;

				for (int k = 1; k < nbins - 2; k++) {
					if (val > t - ddt && t <= t + dt + ddt)
						++Hist(x, y, nbins * c + k);

					t += dt;
				}

				if (nbins - 2 >= 0)
					if (val <= 1 && val > 1 - dt - 2 * ddt)
						++Hist(x, y, nbins * c + nbins - 1);

			}
		}
	}

	return Hist;
}
#endif
