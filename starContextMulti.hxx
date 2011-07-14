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
//using namespace std;

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
/*
template <class IND, class T>
void average_features(NumpyArray<1, Singleband<IND> >& sizes,
                      IND x, IND y, IND c, NumpyArray<3, Multiband<T> >& predictions,
                      std::vector<T>& averages)
{
    //this function computes average prediction for class c in squares of size specified
    //in sizes. the returned average only counts the points in the outside rim of the square
    //and does not count the ones, already included in the smaller squares.
    
    int ns = sizes.size();
    std::vector<T> full;
    for (int is=0; is<ns; ++is){
        T pred = average_pred(x, y, c, is, predictions);
        full.push_back(pred);
        if (is>1){
            T hollow = full[is]-full[is-1]*(is-1)*(is-1)/(is*is);
            averages[is] = hollow;
        } else {
            averages[is] = full[is];
        }
    }
}
*/
template <class IND, class T, class S1, class S2>
void average_features_2(MultiArrayView<1, IND, S1>& radii,
                        IND x, IND y, IND c, 
                        MultiArrayView<3, T, S1>& predictions,
                        MultiArrayView<3, T, S2>& integral,
                        std::vector<T>& averages)
{
    int nr = radii.size();
    int nclasses = predictions.shape()[2];
    //std::cout<<"predictions shape: "<<predictions.shape()[0]<<" "<<predictions.shape()[1]<<" "<<predictions.shape()[2]<<std::endl;
    for (int ir=0; ir<nr; ++ir){
        IND xminus = 0;
        IND yminus = 0;
        if (x<radii[ir] || y<radii[ir] || x+radii[ir]>predictions.shape()[0]-1 || y+radii[ir]>predictions.shape()[1]-1){
            averages[ir]= 1./nclasses;
            continue;
        } 
        
        T ul = (x==radii[ir] || y==radii[ir]) ? 0 : integral(x-radii[ir]-1, y-radii[ir]-1, c);
        T ll = (y==radii[ir]) ? 0 : integral(x+radii[ir], y-radii[ir]-1, c);
        T ur = (x==radii[ir]) ? 0 : integral(x-radii[ir]-1, y+radii[ir], c);
        T lr = integral(x+radii[ir], y+radii[ir], c);
        
        T sum = lr-ll-ur+ul;
        int n = (2*radii[ir]+1)*(2*radii[ir]+1);
        if (ir>0){
            T sum_prev = averages[ir-1]*(2*radii[ir-1]+1)*(2*radii[ir-1]+1);
            if (x==2 && y==2 && c==0 && ir==1){
                std::cout<<"sum= "<<sum<<", sum_prev= "<<sum_prev<<std::endl;
                std::cout<<"averages[ir-1]="<<averages[ir-1]<<std::endl;
            }
            sum-=sum_prev;
            n-=(2*radii[ir-1]+1)*(2*radii[ir-1]+1);
        }
        averages[ir]=sum/n;
        if (x==2 && y==2 && c==0 && ir==1){
            std::cout<<"c= "<<c<<" ,integral: "<<std::endl;
            /*
            std::cout<<integral(0, 0, 0)<<" "<<integral(0, 1, 0)<<" "<<integral(0, 2, 0)<<" "<<integral(0, 3, 0)<<std::endl;
            std::cout<<integral(1, 0, 0)<<" "<<integral(1, 1, 0)<<" "<<integral(1, 2, 0)<<" "<<integral(1, 3, 0)<<std::endl;
            std::cout<<integral(2, 0, 0)<<" "<<integral(2, 1, 0)<<" "<<integral(2, 2, 0)<<" "<<integral(2, 3, 0)<<std::endl;
            std::cout<<integral(3, 0, 0)<<" "<<integral(3, 1, 0)<<" "<<integral(3, 2, 0)<<" "<<integral(3, 3, 0)<<std::endl;
            */
            std::cout<<"sum="<<sum<<" , radii[ir]="<<radii[ir]<<std::endl;
            std::cout<<"ul="<<ul<<" , ur="<<ur<<" ,ll="<<ll<<" ,lr="<<lr<<std::endl;
            std::cout<<"ir = "<<ir<<" ,averages[ir]= "<<averages[ir]<<std::endl;
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

template <class IND, class T, class S>
void avContext2Dmulti(MultiArrayView<1, IND, S>& sizes,
                      MultiArrayView<3, T, S>& predictions,
                      MultiArrayView<3, T, S>& res)
{
    int nx = predictions.shape()[0];
    int ny = predictions.shape()[1];
    int nclasses = predictions.shape()[2];
    int nnewfeatures = sizes.size();
    MultiArray<3, T> integral(predictions.shape());
    
    integralImage(predictions, integral);
    
    for (IND c=0; c<nclasses; ++c) {
        std::cout<<"class "<<c<<std::endl;
        for (IND x=0; x<nx; ++x){
            for (IND y=0; y<ny; ++y){
                std::vector<T> newf(nnewfeatures);
                average_features_2(sizes, x, y, c, predictions, integral, newf);
                for (IND ii=0; ii<nnewfeatures; ++ii){
                    res(x, y, c*nnewfeatures + ii) = newf[ii];
                }
            }
        }
    }
    return;
}
    
    
    
#endif
