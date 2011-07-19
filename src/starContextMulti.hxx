#ifndef STARCONTEXTMULTI_HXX
#define STARCONTEXTMULTI_HXX

#include <iostream>
#include <vector>
#include <limits>

#include <vigra/multi_array.hxx>
#include <vigra/numpy_array.hxx>
#include <vigra/numpy_array_converters.hxx>
#include <vigra/multi_pointoperators.hxx>
#include <vigra/utilities.hxx>

#include "integralImage.hxx"

using namespace vigra;

template <class IND, class T, class S>
void new_features(MultiArrayView<1, IND, S>& radii,
                         IND x, IND y, IND c, MultiArrayView<3, T, S>& predictions,
                         std::vector<T>& neighbors)
{
    //this function finds predictions of the neighbor points and puts them into the neighbors array
    //in 2D. The order is (x-, y-), (x-, y), (x-, y+), (x, y-), (x, y+), (x+, y-), (x+, y), (x+, y+)
    int nr = radii.size();
    int nclasses = predictions.shape()[2];
    int nx = predictions.shape()[0];
    int ny = predictions.shape()[1];
    int nav = 3;
    int nn = neighbors.size()/nr;
    int nn2 = nn/2;
    bool wa = 1; //with averages
    for (int ir=0; ir<nr; ++ir) {
        IND xminus = x - radii[ir];
        IND xplus = x + radii[ir];
        IND yminus = y - radii[ir];
        IND yplus = y + radii[ir];
        
        if (x<radii[ir]) {
            neighbors[ir*nn + 0] = 1./nclasses;
            neighbors[ir*nn + 1] = 1./nclasses;
            neighbors[ir*nn + 2] = 1./nclasses;
            if (wa) {
                
                neighbors[ir*nn + nn2 + 0] = 1./nclasses;
                neighbors[ir*nn + nn2 + 1] = 1./nclasses;
                neighbors[ir*nn + nn2 +2] = 1./nclasses;
            }
        } else {
            if (y<radii[ir]) {
                neighbors[ir*nn + 0] = 1./nclasses;
                if (wa) neighbors[ir*nn+nn2+0] = 1./nclasses;
            } else {
                neighbors[ir*nn + 0] = predictions(xminus, yminus, c);
                if (wa) neighbors[ir*nn+nn2+0] = average_pred(xminus, yminus, c, nav, predictions);
                
            }
            neighbors[1] = predictions(xminus, y, c);
            if (wa) neighbors[ir*nn+nn2+1] = average_pred(xminus, y, c, nav, predictions);
            if (yplus>=ny) {
                neighbors[ir*nn + 2] = 1./nclasses;
                if (wa) neighbors[ir*nn+nn2+2] = 1./nclasses;
            } else {
                neighbors[ir*nn + 2] = predictions(xminus, yplus, c);
                if (wa) neighbors[ir*nn+nn2+2] = average_pred(xminus, yplus, c, nav, predictions);
                
            }
        }
        if (y<radii[ir]) {
            neighbors[ir*nn+3]=1./nclasses;
            if (wa) neighbors[ir*nn+nn2+3] = 1./nclasses;
        } else {
            neighbors[ir*nn+3]= predictions(x, yminus, c);
            if (wa) neighbors[ir*nn+nn2+3] = average_pred(x, yminus, c, nav, predictions);
        }
        if (yplus>=ny){
            neighbors[ir*nn+4]=1./nclasses;
            if (wa) neighbors[ir*nn+nn2+4] = 1./nclasses;
        } else {
            neighbors[ir*nn+4]= predictions(x, yplus, c);            
            if (wa) neighbors[ir*nn+nn2+4] = average_pred(x, yplus, c, nav, predictions);
        }
        if (xplus >= nx) {
            neighbors[ir*nn + 5] = 1./nclasses;
            neighbors[ir*nn + 6] = 1./nclasses;
            neighbors[ir*nn + 7] = 1./nclasses;
            if (wa) {
                neighbors[ir*nn + nn2 + 5] = 1./nclasses;
                neighbors[ir*nn + nn2 + 6] = 1./nclasses;
                neighbors[ir*nn + nn2 + 7] = 1./nclasses;
            }
        } else {
            if (y<radii[ir]) {
                neighbors[ir*nn + 5] = 1./nclasses;
                if (wa) neighbors[ir*nn+nn2+5] = 1./nclasses;
            } else {
                neighbors[ir*nn + 5] = predictions(xplus, yminus, c);
                if (wa) neighbors[ir*nn+nn2+5] = average_pred(xplus, yminus, c, nav, predictions);
            }
            neighbors[ir*nn + 6] = predictions(xplus, y, c);
            if (wa) neighbors[ir*nn+nn2+6] = average_pred(xplus, y, c, nav, predictions);
            if (yplus>=ny) {
                neighbors[ir*nn + 7] = 1./nclasses;
                if (wa) neighbors[ir*nn+nn2+7] = 1./nclasses;
            } else {
                neighbors[ir*nn + 7] = predictions(xplus, yplus, c);
                if (wa) neighbors[ir*nn+nn2+7] = average_pred(xplus, yplus, c, nav, predictions);
            }
        }
    }
    return;
        
}

template <class IND, class T, class S1>
void starFeatures3Dvar(std::vector<IND>& xvars,
                       std::vector<IND>& yvars,
                       std::vector<IND>& zvars,
                       IND c,
                       MultiArrayView<4, T, S1>& predictions, 
                       std::vector<T>& neighbors)
{
    IND nclasses = predictions.shape()[3];
    typename std::vector<IND>::iterator xit;
    typename std::vector<IND>::iterator yit;
    typename std::vector<IND>::iterator zit;
    int iflat = 0;
    for (xit=xvars.begin(); xit!=xvars.end(); ++xit){
        if ((*xit)==std::numeric_limits<IND>::max()){
            //x too big or too small, set all to equal probability
            for (yit=yvars.begin(); yit!=yvars.end(); ++yit){
                for (zit=zvars.begin(); zit!=zvars.end(); ++zit){                    
                    neighbors[iflat]=1./nclasses;
                    iflat++;
                }
            }
        } else {
            for (yit=yvars.begin(); yit!=yvars.end(); ++yit){
                if ((*yit)==std::numeric_limits<IND>::max()){
                    for (zit=zvars.begin(); zit!=zvars.end(); ++zit){
                        neighbors[iflat]=1./nclasses;
                        iflat++;
                    }
                } else {
                    for (zit=zvars.begin(); zit!=zvars.end(); ++zit){
                        if ((*zit)==std::numeric_limits<IND>::max()){
                            neighbors[iflat]=1./nclasses;
                            iflat++;
                        } else {
                            neighbors[iflat]=predictions((*xit), (*yit), (*zit), c);
                        }
                    }
                }
            }
        }
    }
    
    
    return;
    
}



template <class IND, class T, class S>
T average_pred(IND x, IND y, IND c, int nav, MultiArrayView<3, T, S>& predictions)
{
    //this function computes the average of predictions in nav_x_nav neighborhoods
    //
    T sum = 0;
    int n = 0;
    int nclasses = predictions.shape()[2];
    int nx = predictions.shape()[0];
    int ny = predictions.shape()[1];
    int lim = (nav-1)/2;
    if (x<lim) {
        return 1./nclasses;
    }
    if (y<lim) {
        return 1./nclasses;
    }
    if (x>=nx-lim) {
        return 1./nclasses;
    }
    if (y>=ny-lim) {
        return 1./nclasses;
    }
    
    for (IND ix = x-lim; ix<x+lim+1; ++ix) {
        for (IND iy = y-lim; iy<y+lim+1; ++iy) {
            sum+=predictions(ix, iy, c);
            n++;
        }
    }
    return sum/n;
}

template <class IND, class T, class S>
void starContext3Dvar(MultiArrayView<1, IND, S>& radii_x,
                      MultiArrayView<1, IND, S>& radii_y,
                      MultiArrayView<1, IND, S>& radii_z,
                      MultiArrayView<4, T, S>& predictions,
                      MultiArrayView<4, T, S>& res)
{
    
    std::cout<<"stride order: "<<predictions.strideOrdering()<<std::endl;
    std::cout<<"strides: "<<predictions.stride()<<std::endl;
    int nx = predictions.shape()[0];
    int ny = predictions.shape()[1];
    int nz = predictions.shape()[2];
    int nclasses = predictions.shape()[3];
    int nrx = radii_x.shape()[0];
    int nry = radii_y.shape()[0];
    int nrz = radii_z.shape()[0];
    //each radius gives 3 points: xminus, x, xplus
    //FIXME: but we have to subtract 1 for the point itself
    //only predictions for now, no averages
    int nnewfeatures = nrx*nry*nrz*27;
    std::vector<IND> xvars(nrx*3);
    std::vector<IND> yvars(nry*3);
    std::vector<IND> zvars(nrz*3);
    for (IND x=0; x<nx; ++x){
        //std::cout<<"class "<<c<<std::endl;
        int ixvar=0;
        for (IND irx=0; irx<nrx; ++x){
            xvars[ixvar] = (x<irx) ? std::numeric_limits<IND>::max() : x-irx;
            xvars[ixvar+1] = x;
            xvars[ixvar+2] = (x+irx>=nx) ? std::numeric_limits<IND>::max() : x+irx;
            ixvar+=3;
        }
        for (IND y=0; y<ny; ++y){
            int iyvar = 0;
            for (IND iry=0; iry<nry; ++y){
                yvars[iyvar] = (y<iry) ? std::numeric_limits<IND>::max() : y-iry;
                yvars[iyvar+1] = y;
                yvars[iyvar+2] = (y+iry>=ny) ? std::numeric_limits<IND>::max() : y+iry;
                iyvar+=3;
            }
            for (IND z=0; y<nz; ++z){
                int izvar = 0;
                for (IND irz=0; irz<nrz; ++z){
                    zvars[izvar] = (z<irz) ? std::numeric_limits<IND>::max() : z-irz;
                    zvars[izvar+1] = z;
                    zvars[izvar+2] = (z+irz>=nz) ? std::numeric_limits<IND>::max() : z+irz;
                    izvar+=3;
                }
                for (IND c=0; c<nclasses; ++c){
                    std::vector<T> neighbors(nnewfeatures);
                    starFeatures3Dvar(xvars, yvars, zvars, c, predictions, neighbors);
                    for (IND ii=0; ii<nnewfeatures; ++ii){
                        res(x, y, z, c*nnewfeatures+ii) = neighbors[ii];
                    }
                }
            }
        }
    }
    return;
}


template <class IND, class T, class S>
void starContext2Dmulti(MultiArrayView<1, IND, S>& radii,
                        MultiArrayView<3, T, S>& predictions,
                        MultiArrayView<3, T, S>& res)
{
    std::cout<<"shape of predictions: "<<predictions.shape()<<std::endl;
    std::cout<<"shape of results: "<<res.shape()<<std::endl;
    std::cout<<"stride order: "<<predictions.strideOrdering()<<std::endl;
    std::cout<<"strides: "<<predictions.stride()<<std::endl;
    int nx = predictions.shape()[0];
    int ny = predictions.shape()[1];
    int nclasses = predictions.shape()[2];
    int nnewfeatures = radii.size()*8*2;
    for (IND c=0; c<nclasses; ++c){
        std::cout<<"class "<<c<<std::endl;
        for (IND x=0; x<nx; ++x){
            for (IND y=0; y<ny; ++y){
                std::vector<T> neighbors(nnewfeatures);
                new_features(radii, x, y, c, predictions, neighbors);
                for (IND ii=0; ii<nnewfeatures; ++ii){
                    res(x, y, c*nnewfeatures + ii) = neighbors[ii];
                    
                }
            }
        }
    }
    return;
}


    
#endif
