#ifndef CONTEXTAVERAGE_HXX
#define CONTEXTAVERAGE_HXX

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

template <class IND, class T, class S1, class S2>
void average_features_2(MultiArrayView<1, IND, S1>& radii,
                        IND x, IND y, IND c, 
                        MultiArrayView<3, T, S2>& integral,
                        std::vector<T>& averages)
{
    int nr = radii.size();
    int nclasses = integral.shape()[2];
    //std::cout<<"predictions shape: "<<predictions.shape()[0]<<" "<<predictions.shape()[1]<<" "<<predictions.shape()[2]<<std::endl;
    for (int ir=0; ir<nr; ++ir){
        IND xminus = 0;
        IND yminus = 0;
        if (x<radii[ir] || y<radii[ir] || x+radii[ir]>integral.shape()[0]-1 || y+radii[ir]>integral.shape()[1]-1){
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
            sum-=sum_prev;
            n-=(2*radii[ir-1]+1)*(2*radii[ir-1]+1);
        }
        averages[ir]=sum/n;

    }
    return;
}

/*
template <class IND, class T, class S>
void replicate_z(IND x, IND y, IND z, IND c,
                 MultiArrayView<4, T, S>& res,
                 MultiArrayView<1, IND, S>& sizes, 
                 std::vector<T>& neighbors)
{
    int ns = sizes.shape()[0];
    int nx = res.shape()[0];
    int ny = res.shape()[1];
    int nz = res.shape()[2];
    int nnewf = neighbors.size()
    for (int is=0; is<ns; ++is) {
        //reflect
        for (int ii=0; ii<nnewf; ++ii) {
            res(x, y, z, nnewf+is*(nnewf-1)) = res(x, y, std::abs(z-is), 
    
*/    

template <class IND, class T, class S>
void avContext2Dmulti(MultiArrayView<1, IND, S>& sizes,
                      MultiArrayView<3, T, S>& predictions,
                      MultiArrayView<3, T, S>& res)
{
    //fill the results array with averages of predictions array
    //computed at the radii of sizes of each member of predictions
    
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
                average_features_2(sizes, x, y, c, integral, newf);
                
                for (IND ii=0; ii<nnewfeatures; ++ii){
                    res(x, y, c*nnewfeatures + ii) = newf[ii];
                }
            }
        }
    }
    return;
}
/*
template <class IND, class T, class S>
void avContext3Dslices(MultiArrayView<1, IND, S>& radii,
                       MultiArrayView<1, IND, S>& z_values,
                 MultiArrayView<4, T, S>& predictions,
                 MultiArrayView<4, T, S>& res)
{
    // this function does _not_ compute real 3d averages
    // instead it computes 2d averages in neighborhoods of sizes passed in radii
    // and then adds as features such averages at +- z_values
    
    int nx = predicitons.shape()[0];
    int ny = predictions.shape()[1];
    int nz = predictions.shape()[2];
    int nclasses = predictions.shape()[3];
    int nnewf_slice = radii.shape()[0];
    int nnewf_total = nnewf*z_values.shape()[0];
    MultiArrayShape<3>::type intShp(nx, ny, nclasses);
    MultiArray<3, T> integral(intShp);
    std::vector<T> newf(nnewf_slice);
    
    for (IND z=0; z<nz; ++z){
        MultiArrayView<3, T, StridedArrayTag> pred_slice = predictions.bindAt(2, z);
        integralImage(pred_slice, integral);
        for (IND x=0; x<nx; ++x){
            for (IND y=0; y<ny; ++y){
                for (IND c=0; c<nclasses; ++c){
                    average_features_2(radii, x, y, c, integral, newf);
                    for (IND ii=0; ii<nnewf_slice; ++ii){
                        res(x, y, z, c*nnewf_slice+ii) = newf[ii];
                    }
                }
            }
        }
    }
    
    for (IND x=0; x<nx; ++x){
        for (IND y=0; y<ny; ++y){
            for (IND z=0; z<nz; ++z){
                replicate_z(res, z_values);
            }
        }
    }
}
*/

template <class IND, class T, class S>
void varContext2Dmulti(MultiArrayView<1, IND, S>&sizes,
                       MultiArrayView<3, T, S>& predictions,
                       MultiArrayView<3, T, S>& res)
{
    //fill the results array with averages and variances of predictions array
    //computed at the radii of sizes of each member of predictions
    
    int nx = predictions.shape()[0];
    int ny = predictions.shape()[1];
    int nclasses = predictions.shape()[2];
    
    int nnewfeatures = sizes.size();
    
    MultiArray<3, T> integral(predictions.shape());
    MultiArray<3, T> integral2(predictions.shape());
    
    integralImage(predictions, integral);
    integralImage2(predictions, integral2);

    for (IND c=0; c<nclasses; ++c) {
        std::cout<<"class "<<c<<std::endl;
        for (IND x=0; x<nx; ++x) {
            for (IND y=0; y<ny; ++y) {
                std::vector<T> newf(nnewfeatures);
                average_features_2(sizes, x, y, c, integral, newf);
                std::vector<T> newf2(nnewfeatures);
                average_features_2(sizes, x, y, c, integral2, newf2);
                //fill the averages
                for (IND ii=0; ii<nnewfeatures; ++ii) {
                    res(x, y, c*2*nnewfeatures+ii) = newf[ii];
                }
                //fill the variances
                for (IND ii=0; ii<nnewfeatures; ++ii) {
                    res(x, y, c*2*nnewfeatures+nnewfeatures+ii) = newf2[ii]-newf[ii]*newf[ii];
                }
            }
        }
    }
    return;
}
#endif