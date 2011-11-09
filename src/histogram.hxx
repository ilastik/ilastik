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
    //    nbins -= 1;

    res = value / dt;
    if (res >= nbins)
        throw std::runtime_error(
            "Not implementex for stuff otside ot the interval [0,1]");

    return res;
}


//compute the pixel histogram of a given image
//for multichannel images, compute channelwise
// The input should be a multiarray view last index indicating the channel
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
                float frac_overlap, MultiArrayView<3, T, S2>& Hist) {

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
                                if (val < dt + ddt)
                    ++Hist(x, y, shift+0);
                t += dt;

                for (int k = 1; k < nbins - 1; k++)
                                {
                                        if (val >= t - ddt && val < t + dt + ddt)
                        ++Hist(x, y, shift + k);
                    t += dt;
                }

                if (nbins - 2 >= 0)
                                        if (val <= 1 && val >= 1 - dt - ddt)
                        ++Hist(x, y, shift + (nbins - 1));

            }
        }
    }

}

//compute integral histogram of a given image
//for multichannel images, compute channelwise
// we can choose an amount of overlap beteeen different pixels
// The imput shoudl be a multiarray view last index indicating the channelstd::endl;
// The result is a Histogram where last index loops through the bins
// NB Assumes that the values of each channel in the original image are between 0,1
template<class T1,class T2, class S1, class S2>
void integralHistogram2D(MultiArrayView<3, T1, S1>& image, int nbins,
        MultiArrayView<3, T2, S2>& H) {

    //FIXME you are imposing between zero and 1
    int height = image.shape()[0];
    int width = image.shape()[1];
    int nc = image.shape()[2];
    int x,y,c,index;
    MultiArrayShape<3>::type resShp(width, height, nc * nbins);
    vigra_precondition(resShp[2]==H.shape(2),"wrong shape");

    //For all the channels do the same
    for (c=0;c<nc;c++)
    {
        int shift=c*nbins;
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


template<class T1,class T2, class S1, class S2>
void integralHistogram3D(MultiArrayView<4, T1, S1>& volume, int nbins,
        MultiArrayView<4, T2, S2>& H) 
{
    int nx = volume.shape()[0];
    int ny = volume.shape()[1];
    int nz = volume.shape()[2];
    int nc = volume.shape()[3];
    
    MultiArrayShape<3>::type sliceShp(nx, ny, nc * nbins);
    MultiArray<3, T1> sliceHist(sliceShp);
    
    MultiArrayView<3, T1, StridedArrayTag>  slice = volume.bindAt(2, 0);
    integralHistogram2D(slice, nbins, sliceHist);
    
    for (int ix=0; ix<nx; ++ix){
        for (int iy=0; iy<ny; ++iy){
            for (int ic=0; ic<nc*nbins; ++ic){
                H(ix, iy, 0, ic) = sliceHist(ix, iy, ic);
            }
        }
    }
    
    
    for (int iz=1; iz<nz; ++iz) {
        MultiArrayView<3, T1, StridedArrayTag>  slice = volume.bindAt(2, iz);
        integralHistogram2D(slice, nbins, sliceHist);
        for (int ix=0; ix<nx; ++ix){
            for (int iy=0; iy<ny; ++iy){
                for (int ic=0; ic<nc*nbins; ++ic){
                    H(ix, iy, iz, ic) = H(ix, iy, iz-1, ic)+sliceHist(ix, iy, ic);
                }
            }
        }
    }
}


template<class T1,class T2, class S2>
void integratePixel(T1& val, int x, int y, int nbins,
                    double frac_overlap, int shift, MultiArrayView<3, T2, S2>& Hist) 
{

    double dt = 1 / double(nbins);
    double ddt = dt * frac_overlap;

    double t = 0;

    if (nbins == 1)
    {
        Hist(x,y, shift + 0) ++;
        return;
    }

    if (val < dt + ddt)
            Hist(x, y, shift+0)++;
    t += dt;

    for (int k = 1; k < nbins - 1; k++)
    {
            if (val >= t - ddt && val < t + dt + ddt)
                    Hist(x, y, shift + k)++;
            t += dt;
    }

    if (nbins - 2 >= 0)
            if (val <= 1 && val >= 1 - dt - 1 * ddt)
                    Hist(x, y, shift + (nbins - 1))++;
}

double wfunc(double w){

    return w;

}

template<class T>
double overlapWeighting(double t, double dt, double ddt, T& val ) {

    double w;
    if (val >= t + ddt && val <= t + dt - ddt) return 1;
    else if (val < t + ddt ) w = (val - (t - ddt))/(2*ddt);
    else if (val > t + dt - ddt) w = ((t + dt + ddt - val))/(2*ddt);
    return wfunc(w);
}


template<class T1,class T2, class S2>
void integratePixelWeightLin(T1& val, int x, int y, int nbins,
               double frac_overlap, int shift, MultiArrayView<3, T2, S2>& Hist) 
{

    double dt = 1 / double(nbins);
    double ddt = dt * frac_overlap;

    double t = 0;

    if (nbins == 1)
    {
        Hist(x,y, shift + 0) ++;
        return;
    }

    if (val < dt + ddt)
    {
            if (val< dt- ddt) Hist(x,y,shift+0) ++;
            else Hist(x, y, shift+0) += overlapWeighting(t,dt,ddt,val);
    }
    t += dt;

    for (int k = 1; k < nbins - 1; k++)
    {
            if (val >= t - ddt && val < t + dt + ddt)
                    Hist(x, y, shift + k) += overlapWeighting(t,dt,ddt,val);
            t += dt;
    }

    if (nbins - 2 >= 0)
            if (val <= 1 && val >= 1 - dt - ddt)
            {
                    if (val > 1 - dt + ddt) Hist(x,y,shift + (nbins - 1)) ++;
                    else Hist(x, y, shift + (nbins - 1)) += overlapWeighting(t,dt,ddt,val);
            }
}



template<class T1,class T2, class S2>
void integratePixelWeightGauss(T1& val, int x, int y, int nbins,
               double sigma, int shift, MultiArrayView<3, T2, S2>& Hist) 
{

    const double PI = std::atan(1.0) * 4;
    double dt = 1 / double(nbins);
    double g, m, s;
    m = dt/2;
    s = 0;

    if (nbins == 1)
    {
        Hist(x,y, shift + 0) ++;
        return;
    }

    for (int i = 0; i<nbins; i++)
    {
        s += 1/(sigma * std::sqrt(2 * PI)) * std::exp(-0.5*std::pow((m-val)/sigma,2));
        m += dt;
    }

    m = dt/2;
    for (int i = 0; i<nbins; i++)
    {
        g = 1/(sigma * std::sqrt(2 * PI)) * std::exp(-0.5*std::pow((m-val)/sigma,2));
        Hist(x,y,shift+i) += g/s;
        m += dt;
    }

}




template<class T1,class T2, class S1, class S2>
void integralOverlappingHistogram2D(MultiArrayView<3, T1, S1>& image, int nbins,
               double frac_overlap, MultiArrayView<3, T2, S2>& H) 
{

        //FIXME you are imposing between zero and 1
        int width = image.shape()[0];
        int height = image.shape()[1];
        int nc = image.shape()[2];
        int x,y,c,index;
        MultiArrayShape<3>::type resShp(width, height, nc * nbins);
        vigra_precondition(resShp[2]==H.shape(2),"wrong shape");
        vigra_precondition(frac_overlap>=0 && frac_overlap<1,"fractionary overlap between [0,1)");


        std::cerr << "inside c++" << std::endl;
        //For all the channels do the same
        for (c=0;c<nc;c++)
        {
                int shift=c*nbins;
                //std::cerr << "here" << std::endl ;

                //initialize the histogram
                for(int j=shift; j<nbins+shift;j++)  H(0,0,j)=0;

                integratePixel(image(0,0,c),0,0, nbins,frac_overlap,shift,H);


                for (y=1;y<height;y++)
                {
                        for(int j=shift; j<nbins+shift;j++)  H(0,y,j)=H(0,y-1,j);

                        integratePixel(image(0,y,c),0,y, nbins,frac_overlap,shift,H);
                }

                for (x=1;x<width;x++)
                {                       
                        for(int j=shift; j<nbins+shift;j++)   H(x,0,j)=H(x-1,0,j);

                        integratePixel(image(x,0,c),x,0, nbins,frac_overlap,shift,H);
                }

                for (y=1;y<height;y++)
                        for(x=1;x<width;x++)
                        {
                                for(int j=shift; j<nbins+shift;j++)  H(x,y,j)=H(x,y-1,j)+H(x-1,y,j)-H(x-1,y-1,j);

                                integratePixel(image(x,y,c),x,y, nbins,frac_overlap,shift,H);
                        }

        }

}


template<class T1,class T2, class S1, class S2>
void integralOverlappingWeightLinHistogram2D(MultiArrayView<3, T1, S1>& image, int nbins,
               double frac_overlap, MultiArrayView<3, T2, S2>& H) 
{
        //FIXME you are imposing between zero and 1
        int width = image.shape()[0];
        int height = image.shape()[1];
        int nc = image.shape()[2];
        int x,y,c,index;
        MultiArrayShape<3>::type resShp(width, height, nc * nbins);
        vigra_precondition(resShp[2]==H.shape(2),"wrong shape");
        vigra_precondition(frac_overlap>=0 && frac_overlap<1,"fractionary overlap between [0,1)");


        std::cerr << "inside c++" << std::endl;
        //For all the channels do the same
        for (c=0;c<nc;c++)
        {
                int shift=c*nbins;
                //std::cerr << "here" << std::endl ;

                //initialize the histogram
                for(int j=shift; j<nbins+shift;j++)  H(0,0,j)=0;

                integratePixelWeightLin(image(0,0,c),0,0, nbins,frac_overlap,shift,H);


                for (y=1;y<height;y++)
                {
                        for(int j=shift; j<nbins+shift;j++)  H(0,y,j)=H(0,y-1,j);

                        integratePixelWeightLin(image(0,y,c),0,y, nbins,frac_overlap,shift,H);
                }

                for (x=1;x<width;x++)
                {
                        for(int j=shift; j<nbins+shift;j++)   H(x,0,j)=H(x-1,0,j);

                        integratePixelWeightLin(image(x,0,c),x,0, nbins,frac_overlap,shift,H);
                }

                for (y=1;y<height;y++)
                        for(x=1;x<width;x++)
                        {
                                for(int j=shift; j<nbins+shift;j++)  H(x,y,j)=H(x-1,y,j)+H(x,y-1,j)-H(x-1,y-1,j);

                                integratePixelWeightLin(image(x,y,c),x,y, nbins,frac_overlap,shift,H);
                        }

        }

}



template<class T1,class T2, class S1, class S2>
void integralOverlappingWeightGaussHistogram2D(MultiArrayView<3, T1, S1>& image, int nbins,
               double sigma, MultiArrayView<3, T2, S2>& H) 
{
        //FIXME you are imposing between zero and 1
        int width = image.shape()[0];
        int height = image.shape()[1];
        int nc = image.shape()[2];
        int x,y,c,index;
        MultiArrayShape<3>::type resShp(width, height, nc * nbins);
        vigra_precondition(resShp[2]==H.shape(2),"wrong shape");
        vigra_precondition(sigma>0 ,"sigam greater should be than 0");

        std::cerr << "inside c++" << std::endl;
        //For all the channels do the same
        for (c=0;c<nc;c++)
        {
                int shift=c*nbins;
                //std::cerr << "here" << std::endl ;

                //initialize the histogram
                for(int j=shift; j<nbins+shift;j++)  H(0,0,j)=0;

                integratePixelWeightGauss(image(0,0,c),0,0, nbins,sigma,shift,H);


                for (y=1;y<height;y++)
                {
                        for(int j=shift; j<nbins+shift;j++)  H(0,y,j)=H(0,y-1,j);

                        integratePixelWeightGauss(image(0,y,c),0,y, nbins,sigma,shift,H);
                }

                for (x=1;x<width;x++)
                {
                        for(int j=shift; j<nbins+shift;j++)   H(x,0,j)=H(x-1,0,j);

                        integratePixelWeightGauss(image(x,0,c),x,0, nbins,sigma,shift,H);
                }

                for (y=1;y<height;y++)
                        for(x=1;x<width;x++)
                        {
                                for(int j=shift; j<nbins+shift;j++)  H(x,y,j)=H(x-1,y,j)+H(x,y-1,j)-H(x-1,y-1,j);

                                integratePixelWeightGauss(image(x,y,c),x,y, nbins,sigma,shift,H);
                        }

        }

}

template<class T, class S1, class S2>
void overlappingWeightLinHistogram2D(MultiArrayView<3, T, S1>& image, int nbins,
                double frac_overlap, MultiArrayView<3, T, S2>& Hist) {


        int width = image.shape()[0];
        int height = image.shape()[1];
        int nc = image.shape()[2];

        MultiArrayShape<3>::type resShp(width, height, nc * nbins);
        vigra_precondition(resShp[2]==Hist.shape(2),"wrong shape");
        vigra_precondition(frac_overlap>=0 && frac_overlap<1,"fractionary overlap between [0,1)");

        int x, y, c;

        //Do this for all the channels
        for (c = 0; c < nc; c++)
        {
                int shift=nbins*c; //shift to write the result to corret bin

                for (y = 0; y < height; y++)
                {
                        for (x = 0; x < width; x++)  integratePixelWeightLin(image(x,y,c),x,y,nbins,frac_overlap,shift,Hist);

                }
        }

}


template<class T, class S1, class S2>
void overlappingWeightGaussHistogram2D(MultiArrayView<3, T, S1>& image, int nbins,
                double sigma, MultiArrayView<3, T, S2>& Hist) {


        int width = image.shape()[0];
        int height = image.shape()[1];
        int nc = image.shape()[2];

        MultiArrayShape<3>::type resShp(width, height, nc * nbins);
        vigra_precondition(resShp[2]==Hist.shape(2),"wrong shape");
        vigra_precondition(sigma>0 ,"sigma should be greater than 0");

        int x, y, c;

        //Do this for all the channels
        for (c = 0; c < nc; c++)
        {
                int shift=nbins*c; //shift to write the result to corret bin

                for (y = 0; y < height; y++)
                {
                        for (x = 0; x < width; x++)  integratePixelWeightGauss(image(x,y,c),x,y,nbins,sigma,shift,Hist);

                }
        }

}


template<class IND, class T1,class T2, class S1, class S2>
void contextHistogram2D(MultiArrayView<1, IND, S1>&radii, int nbins, 
                        MultiArrayView<3, T1, S1>& image, 
                        MultiArrayView<3, T2, S2>& res) 
{
    //this function computes histograms of the image. 
    //the histograms are computed in concentric squares of size radii,
    //where  for each r_i the middle of the square of size r_i-1 is removed
    //for multichannel images, histogramming is done channel-wise
    
    int nx = image.shape()[0];
    int ny = image.shape()[1];
    int nchannels = image.shape()[2];
    int nr = radii.shape()[0];
    
    int nctb = nchannels*nbins;
    int nnewfeatures = nr*nctb;
    MultiArrayShape<3>::type resShp(nx, ny, nctb);
    MultiArray<3, T1> integral(resShp);
    integralHistogram2D(image, nbins, integral);
    
    std::vector<T1> flathisto(nnewfeatures);
    //just to avoid allocating these vectors at each iteration
    std::vector<T1> lr(nctb);
    std::vector<T1> ur(nctb);
    std::vector<T1> ll(nctb);
    std::vector<T1> ul(nctb);
    
    for (int ix=0; ix<nx; ++ix){
        for (int iy=0; iy<ny; ++iy){
            contextHistogramFeatures2D(ix, iy, nchannels, lr, ll, ur, ul, radii, integral, flathisto);
            for (int ii=0; ii<nnewfeatures; ++ii){
                res(ix, iy, ii) = flathisto[ii];
            }
        }
    }
}

template <class IND, class T1, class S1, class S2>
void contextHistogramFeatures2D(int x, int y, int nclasses,
                              std::vector<T1>& lr, std::vector<T1>& ll,
                              std::vector<T1>& ur, std::vector<T1>& ul,
                              MultiArrayView<1, IND, S1>& radii,
                              MultiArrayView<3, T1, S2>& integral,
                              std::vector<T1>& flathisto)
{
    
    int nr = radii.shape()[0];
    int nctb = integral.shape()[2];
    
    for (int ir=0; ir<nr; ++ir){
        if (x<radii[ir] || y<radii[ir] || x+radii[ir]>integral.shape()[0]-1 || y+radii[ir]>integral.shape()[1]-1){
            //FIXME: later, use reflection for out-of-bounds stuff
            for (int ibin=0; ibin<nctb; ++ibin){
                flathisto[ir*nctb + ibin] = 1./nclasses;
            }
            continue;
        } 
        for (int ibin=0; ibin<nctb; ++ibin){
            ul[ibin] = (x==radii[ir] || y==radii[ir]) ? 0 : integral(x-radii[ir]-1, y-radii[ir]-1, ibin);
            ll[ibin] = (y==radii[ir]) ? 0 : integral(x+radii[ir], y-radii[ir]-1, ibin);
            ur[ibin] = (x==radii[ir]) ? 0 : integral(x-radii[ir]-1, y+radii[ir], ibin);
            lr[ibin] = integral(x+radii[ir], y+radii[ir], ibin);
    
            flathisto[ir*nctb + ibin] = lr[ibin]-ll[ibin]-ur[ibin]+ul[ibin];
            if (ir>0){
                flathisto[ir*nctb + ibin]-=flathisto[(ir-1)*nctb + ibin];
            }
        }
    }
    return;
}

template<class IND, class T1,class T2, class S1, class S2>
void contextHistogram3D(MultiArrayView<2, IND, S1>&radii, int nbins, 
                        MultiArrayView<4, T1, S1>& volume, 
                        MultiArrayView<4, T2, S2>& res) 
{
    //this function computes histograms of the image. 
    //the histograms are computed in concentric rectangles of size, defined by radii,
    //where  for each r_i the middle of the square of size r_i-1 is removed
    //for multichannel images, histogramming is done channel-wise
    //The radii don't have to be the same in all dimensions and should be specified as:
    //[[r1_x, r1_y, r1_z], [r2_x, r2_y, r2_z],...]
    
    int nx = volume.shape()[0];
    int ny = volume.shape()[1];
    int nz = volume.shape()[2];
    int nchannels = volume.shape()[3];
    int nr = radii.shape()[0];
    
    int nctb = nchannels*nbins;
    int nnewfeatures = nr*nctb;
    MultiArrayShape<4>::type resShp(nx, ny, nz, nctb);
    MultiArray<4, T1> integral(resShp);
    integralHistogram3D(volume, nbins, integral);
    
    std::vector<T1> flathisto(nnewfeatures);
    //just to avoid allocating these vectors at each iteration
    std::vector<T1> llr(nctb);
    std::vector<T1> lur(nctb);
    std::vector<T1> lll(nctb);
    std::vector<T1> lul(nctb);
    std::vector<T1> ulr(nctb);
    std::vector<T1> uur(nctb);
    std::vector<T1> ull(nctb);
    std::vector<T1> uul(nctb);
    
    
    for (int ix=0; ix<nx; ++ix){
        for (int iy=0; iy<ny; ++iy){
            for (int iz=0; iz<nz; ++iz){
                contextHistogramFeatures3D(ix, iy, iz, nchannels, llr, lll, lur, lul, ulr, uur, ull, uul, radii, integral, flathisto);
                
                for (int ii=0; ii<nnewfeatures; ++ii){
                    res(ix, iy, iz, ii) = flathisto[ii];
                }
            }
        }
    }
}

template <class IND, class T1, class S1, class S2>
void contextHistogramFeatures3D(int x, int y, int z, int nclasses,
                              std::vector<T1>& llr, std::vector<T1>& lll,
                              std::vector<T1>& lur, std::vector<T1>& lul,
                              std::vector<T1>& ulr, std::vector<T1>& ull,
                              std::vector<T1>& uur, std::vector<T1>& uul,  
                              MultiArrayView<2, IND, S1>& radii,
                              MultiArrayView<4, T1, S2>& integral,
                              std::vector<T1>& flathisto)
{
    
    int nx = integral.shape()[0];
    int ny = integral.shape()[1];
    int nz = integral.shape()[2];
    
    int nr = radii.shape()[0];
    int nctb = integral.shape()[3];
    
    for (int ir=0; ir<nr; ++ir){
        if (x<radii(ir, 0) || y<radii(ir, 1) || z<radii(ir, 2) || x+radii(ir, 0)>nx-1 || y+radii(ir,1)>ny-1 || z+radii(ir, 2)>nz-1){
            //FIXME: later, use reflection for out-of-bounds stuff
            for (int ibin=0; ibin<nctb; ++ibin){
                flathisto[ir*nctb + ibin] = 1./nclasses;
            }
            continue;
        } 
        for (int ibin=0; ibin<nctb; ++ibin){
            
            uul[ibin] = (x==radii(ir,0) || y==radii(ir,1) || z==radii(ir,2)) ? 0 : integral(x-radii(ir,0)-1, y-radii(ir,1)-1, z-radii(ir,2)-1, ibin);
            ull[ibin] = (y==radii(ir, 1) || z==radii(ir,2)) ? 0 : integral(x+radii(ir,0), y-radii(ir, 1)-1, z-radii(ir,2)-1, ibin);
            uur[ibin] = (x==radii(ir,0) || z==radii(ir,2)) ? 0 : integral(x-radii(ir,0)-1, y+radii(ir, 1), z-radii(ir,2)-1, ibin);
            ulr[ibin] = (z==radii(ir, 2)) ? 0 : integral(x+radii(ir,0), y+radii(ir, 1), z-radii(ir, 2)-1, ibin);
            
            lul[ibin] = (x==radii(ir,0) || y==radii(ir, 1)) ? 0 : integral(x-radii(ir,0)-1, y-radii[ir]-1, z+radii(ir, 2), ibin);
            lll[ibin] = (y==radii(ir,1)) ? 0 : integral(x+radii(ir,0), y-radii(ir,1)-1, z+radii(ir,2), ibin);
            lur[ibin] = (x==radii(ir,0)) ? 0 : integral(x-radii(ir,0)-1, y+radii(ir,1), z+radii(ir,2), ibin);
            llr[ibin] = integral(x+radii(ir,0), y+radii(ir, 1), z+radii(ir, 2), ibin);
 
            //T sum = uur + ull + llr + lul - ulr - uul - lur -lll;
            
            /*
            ul[ibin] = (x==radii[ir] || y==radii[ir]) ? 0 : integral(x-radii[ir]-1, y-radii[ir]-1, ibin);
            ll[ibin] = (y==radii[ir]) ? 0 : integral(x+radii[ir], y-radii[ir]-1, ibin);
            ur[ibin] = (x==radii[ir]) ? 0 : integral(x-radii[ir]-1, y+radii[ir], ibin);
            lr[ibin] = integral(x+radii[ir], y+radii[ir], ibin);
            */
            //flathisto[ir*nctb + ibin] = lr[ibin]-ll[ibin]-ur[ibin]+ul[ibin];
            flathisto[ir*nctb + ibin] = uur[ibin]+ull[ibin]+llr[ibin]+lul[ibin]-ulr[ibin]-uul[ibin]-lur[ibin]-lll[ibin];
            
            if (ir>0){
                flathisto[ir*nctb + ibin]-=flathisto[(ir-1)*nctb + ibin];
            }
        }
    }
    return;
}

    
    
#endif
