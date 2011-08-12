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

template <class IND, class T, class S>
void starFeatures3DvarNew(IND x, IND y, IND z, IND c,
                          MultiArrayView<2, IND, S>& triplets,
                          MultiArrayView<4, T, S>& predictions,
                          std::vector<T>& neighbors)
{
    int nx = predictions.shape()[0];
    int ny = predictions.shape()[1];
    int nz = predictions.shape()[2];
    int nclasses = predictions.shape()[3];
    
    int nr = triplets.shape()[0];
    //order: x-, y-, z-; x-,y-,z; x-,y-,z+; 
    //       x-, y, z-; x-,y, z, x-,y,z+;
    //       x-, y+,z-; x-,y+,z; x-,y+,z+;
    //       ...
    
    bool xminus, xplus, yminus, yplus, zminus, zplus;
    for (int r=0; r<nr; ++r) {
        IND rx = triplets(r, 0);
        IND ry = triplets(r, 1);
        IND rz = triplets(r, 2);
        
        xminus = (x>=rx);
        xplus = (x+rx<nx);
        yminus = (y>=ry);
        yplus = (y+ry<ny);
        zminus = (z>=rz);
        zplus = (z+rz<nz);
        
        neighbors[r*26 + 0] =  (xminus && yminus && zminus) ?   predictions(x-rx, y-ry, z-rz, c) : 1./nclasses;
        neighbors[r*26 +1] =  (xminus && yminus) ?              predictions(x-rx, y-ry, z, c) : 1./nclasses;
        neighbors[r*26 +2] =  (xminus && yminus && zplus) ?     predictions(x-rx, y-ry, z+rz, c) : 1./nclasses;
        
        neighbors[r*26 +3] =  (xminus && zminus) ?            predictions(x-rx, y, z-rz, c) : 1./nclasses;
        neighbors[r*26 +4] =  (xminus) ?                      predictions(x-rx, y, z, c) : 1./nclasses;
        neighbors[r*26 +5] =  (xminus && zplus) ?             predictions(x-rx, y, z+rz, c) : 1./nclasses;
        
        neighbors[r*26 +6] =  (xminus && yplus && zminus) ? predictions(x-rx, y+ry, z-rz, c) : 1./nclasses;
        neighbors[r*26 +7] =  (xminus && yplus) ?           predictions(x-rx, y+ry, z, c) : 1./nclasses;
        neighbors[r*26 +8] =  (xminus && yplus && zplus) ?  predictions(x-rx, y+ry, z+rz, c) : 1./nclasses;
        /////////////////////////////
        neighbors[r*26 +9] =  (yminus && zminus) ?          predictions(x, y-ry, z-rz, c) : 1./nclasses;
        neighbors[r*26 +10] =  (yminus) ?                   predictions(x, y-ry, z, c) : 1./nclasses;
        neighbors[r*26 +11] =  (yminus && zplus) ?          predictions(x, y-ry, z+rz, c) : 1./nclasses;
        
        neighbors[r*26 +12] =  (zminus) ?                   predictions(x, y, z-rz, c) : 1./nclasses;
        //neighbors[13] =  (xminus) ?                       predictions(x, y, z, c) : 1./nclasses;
        neighbors[r*26 +13] =  (zplus) ?                    predictions(x, y, z+rz, c) : 1./nclasses;
        
        neighbors[r*26 +14] =  (yplus && zminus) ?          predictions(x, y+ry, z-rz, c) : 1./nclasses;
        neighbors[r*26 +15] =  (yplus) ?                    predictions(x, y+ry, z, c) : 1./nclasses;
        neighbors[r*26 +16] =  (yplus && zplus) ?           predictions(x, y+ry, z+rz, c) : 1./nclasses;
        ////////////////////////////
        neighbors[r*26 +17] =  (xplus && yminus && zminus) ?predictions(x+rx, y-ry, z-rz, c) : 1./nclasses;
        neighbors[r*26 +18] =  (xplus && yminus) ?          predictions(x+rx, y-ry, z, c) : 1./nclasses;
        neighbors[r*26 +19] =  (xplus && yminus && zplus) ? predictions(x+rx, y-ry, z+rz, c) : 1./nclasses;
        
        neighbors[r*26 +20] =  (xplus && zminus) ?          predictions(x+rx, y, z-rz, c) : 1./nclasses;
        neighbors[r*26 +21] =  (xplus) ?                    predictions(x+rx, y, z, c) : 1./nclasses;
        neighbors[r*26 +22] =  (xplus && zplus) ?           predictions(x+rx, y, z+rz, c) : 1./nclasses;
        
        neighbors[r*26 +23] =  (xplus && yplus && zminus) ? predictions(x+rx, y+ry, z-rz, c) : 1./nclasses;
        neighbors[r*26 +24] =  (xplus && yplus) ?           predictions(x+rx, y+ry, z, c) : 1./nclasses;
        neighbors[r*26 +25] =  (xplus && yplus && zplus) ?  predictions(x+rx, y+ry, z+rz, c) : 1./nclasses;
 
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
    //the neighborhoods are always symmetric
    //find the original x, y, z point to remove it later
    IND x = xvars[xvars.size()/2];
    IND y = yvars[yvars.size()/2];
    IND z = zvars[zvars.size()/2];
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
                            if ((*xit)==x && (*yit)==y && (*zit)==z){
                                
                                continue;
                            }
                            
                            neighbors[iflat]=predictions((*xit), (*yit), (*zit), c);
                            iflat++;
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
void starContext3Dnew(MultiArrayView<2, IND, S>& radii_triplets,
                      MultiArrayView<4, T, S>& predictions,
                      MultiArrayView<4, T, S>& res)
{
    std::cout<<"stride order: "<<predictions.strideOrdering()<<std::endl;
    std::cout<<"strides: "<<predictions.stride()<<std::endl;
    std::cout<<"predictions shape: "<<predictions.shape()<<std::endl;
    std::cout<<"radii triplets: "<<radii_triplets.shape()<<std::endl;
    int nx = predictions.shape()[0];
    int ny = predictions.shape()[1];
    int nz = predictions.shape()[2];
    int nclasses = predictions.shape()[3];
    int ntr = radii_triplets.shape()[0];
    int nnewfeatures = ntr*26;
    //std::cout<<"nnewfeatures: "<<nnewfeatures<<std::endl;
    std::vector<T> neighbors(nnewfeatures);
    for (IND x=0; x<nx; ++x){
        //std::cout<<"x="<<x<<std::endl;
        for (IND y=0; y<ny; ++y){
            //std::cout<<"y="<<y<<std::endl;
            for (IND z=0; z<nz; ++z){
                //std::cout<<"z="<<z<<std::endl;
                for (IND c=0; c<nclasses; ++c){
                   //std::cout<<"c="<<c<<std::endl;
                   starFeatures3DvarNew(x, y, z, c, radii_triplets, predictions, neighbors);
                   //std::cout<<"function called"<<std::endl;
                   for (int ii=0; ii<ntr*26; ++ii) {
                       res(x, y, z, c*(nnewfeatures-1)+ii) = neighbors[ii];
                   }
                   //std::cout<<"result filled"<<std::endl;
                }
            }
        }
    }
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
    std::cout<<"predictions shape: "<<predictions.shape()<<std::endl;
    int nx = predictions.shape()[0];
    int ny = predictions.shape()[1];
    int nz = predictions.shape()[2];
    int nclasses = predictions.shape()[3];
    std::cout<<"radii shape:"<<radii_x.shape()<<" "<<radii_y.shape()<<" "<<radii_z.shape()<<std::endl;
    int nrx = radii_x.shape()[0];
    int nry = radii_y.shape()[0];
    int nrz = radii_z.shape()[0];
    //each radius gives 3 points: xminus, x, xplus
    //only predictions for now, no averages
    int nnewfeatures = nrx*nry*nrz*26;
    std::vector<IND> xvars(nrx*3);
    std::vector<IND> yvars(nry*3);
    std::vector<IND> zvars(nrz*3);
    std::cout<<"nrx= "<<nrx<<std::endl;
    std::cout<<"starting the loop..."<<std::endl;
    for (IND x=0; x<nx; ++x){
        int ixvar=0;
        for (IND irx=0; irx<nrx; ++irx){
            xvars[ixvar] = (x<radii_x(irx)) ? std::numeric_limits<IND>::max() : x-radii_x(irx);
            xvars[ixvar+1] = x;
            xvars[ixvar+2] = (x+radii_x(irx)>=nx) ? std::numeric_limits<IND>::max() : x+radii_x(irx);
            ixvar+=3;
        }
        for (IND y=0; y<ny; ++y){
            int iyvar = 0;
            for (IND iry=0; iry<nry; ++iry){
                yvars[iyvar] = (y<radii_y(iry)) ? std::numeric_limits<IND>::max() : y-radii_y(iry);
                yvars[iyvar+1] = y;
                yvars[iyvar+2] = (y+radii_y(iry)>=ny) ? std::numeric_limits<IND>::max() : y+radii_y(iry);
                iyvar+=3;
            }
            for (IND z=0; z<nz; ++z){
                int izvar = 0;
                for (IND irz=0; irz<nrz; ++irz){
                    zvars[izvar] = (z<radii_z(irz)) ? std::numeric_limits<IND>::max() : z-radii_z(irz);
                    zvars[izvar+1] = z;
                    zvars[izvar+2] = (z+radii_z(irz)>=nz) ? std::numeric_limits<IND>::max() : z+radii_z(irz);
                    izvar+=3;
                }
                for (IND c=0; c<nclasses; ++c){
                    //std::cout<<"x= "<<x<<", y= "<<y<<", z= "<<z<<", c= "<<c<<std::endl;
                    std::vector<T> neighbors(nnewfeatures);
                    starFeatures3Dvar(xvars, yvars, zvars, c, predictions, neighbors);
                    for (IND ii=0; ii<nnewfeatures; ++ii){
                        //std::cout<<"ii= "<<ii<<", index= "<<c*nnewfeatures+ii<<" ,res.shape: "<<res.shape()
                        //<<", neighbors.size: "<<neighbors.size()<<std::endl;
                        res(x, y, z, c*(nnewfeatures-1)+ii) = neighbors[ii];
                    }
                    //std::cout<<"lkdjflsjdflsjdflsjdf"<<std::endl;
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
