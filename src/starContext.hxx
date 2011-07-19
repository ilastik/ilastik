#ifndef STARCONTEXT_HXX
#define STARCONTEXT_HXX

#include <iostream>
#include <vector>
#include <limits>

#include <vigra/multi_array.hxx>
#include <vigra/numpy_array.hxx>
#include <vigra/numpy_array_converters.hxx>
#include <vigra/multi_pointoperators.hxx>
#include <vigra/utilities.hxx>

using namespace vigra;
//using namespace std;

template <class IND>
void unravel_index(IND index, NumpyArray<1, Singleband<IND> >& fullshape, std::vector<IND>& fullindex)
{
    if (fullshape[1]==1) {
        IND nx = fullshape[2];
        IND y = index/nx;
        IND x = index%nx;
        fullindex[0]= x;
        fullindex[1] = y;
    } else {
        //std::cout<<"linear index: "<<index<< " ";
        //std::cout<<"full shape: "<<fullshape[0]<<" "<<fullshape[0]<<std::endl;
        //it's a weird order, but this way it's the same as in python unravel_indices...
        IND nzny = fullshape[1]*fullshape[2];
        IND nz = fullshape[2];
        IND x = index/nzny;
        IND yz = index % nzny;
        IND y = yz/nz;
        IND z = yz%nz;
        fullindex[0]=x;
        fullindex[1]=y;
        fullindex[2]=z;
    }
    return;
}

template <class IND>
IND ravel_index(IND x, IND y, IND z, NumpyArray<1, Singleband<IND> >& fullshape)
{
    
    if (x > fullshape[0] || x < 0){
        return std::numeric_limits<IND>::max();
    }
    if (y > fullshape[1] || y < 0){
        return std::numeric_limits<IND>::max();
    }
    if (z > fullshape[2] || z < 0){
        return std::numeric_limits<IND>::max();
    }
    
    IND nzny = fullshape[1]*fullshape[2];
    IND total = x*nzny;
    IND nz = fullshape[2];
    total += y*nz;
    total += z;
    return total;
}

template <class IND>
IND ravel_index_2d(IND x, IND y, NumpyArray<1, Singleband<IND> >& fullshape)
{
    
    if (x > fullshape[0] || x < 0){
        return std::numeric_limits<IND>::max();
    }
    if (y > fullshape[1] || y < 0){
        return std::numeric_limits<IND>::max();
    }
    IND nx = fullshape[2];
    IND total = nx*y +x;
    return total;
}



template <class IND>
void neighbor_indices(NumpyArray<1, Singleband<IND> >& radii, 
                      std::vector<IND>& fullindex,
                      NumpyArray<1, Singleband<IND> >& fullshape,
                      std::vector<IND>& neighbors)
{
    //this function finds flat indices of the 26-neighborgood neighbors
    //of a point in 3d, specified by fullindex coordinates
    //these are then pushed into neighbors vector
    
    int nr = radii.size();
    IND x = fullindex[0];
    IND y = fullindex[1];
    IND z = fullindex[2];
    for (int ir=0; ir<nr; ++ir){

        IND xminus = x - radii[ir];
        IND xplus = x + radii[ir];
        IND yminus = y - radii[ir];
        IND yplus = y + radii[ir];
        IND zminus = z - radii[ir];
        IND zplus = z + radii[ir];
        neighbors.push_back(ravel_index(xminus, y, z, fullshape));
        neighbors.push_back(ravel_index(xplus, y, z, fullshape));
        neighbors.push_back(ravel_index(x, yminus, z, fullshape));
        neighbors.push_back(ravel_index(x, yplus, z, fullshape));
        neighbors.push_back(ravel_index(xminus, yminus, z, fullshape));
        neighbors.push_back(ravel_index(xplus, yminus, z, fullshape));
        neighbors.push_back(ravel_index(xminus, yplus, z, fullshape));
        neighbors.push_back(ravel_index(xplus, yplus, z, fullshape));
        
        neighbors.push_back(ravel_index(xminus, y, zminus, fullshape));
        neighbors.push_back(ravel_index(xplus, y, zminus, fullshape));
        neighbors.push_back(ravel_index(x, yminus, zminus, fullshape));
        neighbors.push_back(ravel_index(x, yplus, zminus, fullshape));
        neighbors.push_back(ravel_index(xminus, yminus, zminus, fullshape));
        neighbors.push_back(ravel_index(xplus, yminus, zminus, fullshape));
        neighbors.push_back(ravel_index(xminus, yplus, zminus, fullshape));
        neighbors.push_back(ravel_index(xplus, yplus, zminus, fullshape));       
        neighbors.push_back(ravel_index(x, y, zminus, fullshape));
        
        neighbors.push_back(ravel_index(xminus, y, zplus, fullshape));
        neighbors.push_back(ravel_index(xplus, y, zplus, fullshape));
        neighbors.push_back(ravel_index(x, yminus, zplus, fullshape));
        neighbors.push_back(ravel_index(x, yplus, zplus, fullshape));
        neighbors.push_back(ravel_index(xminus, yminus, zplus, fullshape));
        neighbors.push_back(ravel_index(xplus, yminus, zplus, fullshape));
        neighbors.push_back(ravel_index(xminus, yplus, zplus, fullshape));
        neighbors.push_back(ravel_index(xplus, yplus, zplus, fullshape));       
        neighbors.push_back(ravel_index(x, y, zplus, fullshape));
    }
        
    return;
}                          

template <class IND>
void neighbor_indices_2d(NumpyArray<1, Singleband<IND> >& radii, 
                      std::vector<IND>& fullindex,
                      NumpyArray<1, Singleband<IND> >& fullshape,
                      std::vector<IND>& neighbors)
{
    //this function finds flat indices of the 8-neighborgood neighbors
    //of a point in 2d, specified by fullindex coordinates
    //these are then pushed into neighbors vector
    int nr = radii.size();
    IND x= fullindex[0];
    IND y = fullindex[1];
    for (int ir=0; ir<nr; ++ir) {
        IND xminus = x - radii[ir];
        IND xplus = x + radii[ir];
        IND yminus = y - radii[ir];
        IND yplus = y + radii[ir];
        neighbors.push_back(ravel_index_2d(xminus, y, fullshape));
        neighbors.push_back(ravel_index_2d(xplus, y, fullshape));
        neighbors.push_back(ravel_index_2d(x, yminus, fullshape));
        neighbors.push_back(ravel_index_2d(x, yplus, fullshape));
        neighbors.push_back(ravel_index_2d(xminus, yminus, fullshape));
        neighbors.push_back(ravel_index_2d(xplus, yplus, fullshape));
        neighbors.push_back(ravel_index_2d(xplus, yminus, fullshape));
        neighbors.push_back(ravel_index_2d(xminus, yplus, fullshape));
    }
    return;
}

/*
template <class IND, class T>
void new_features(NumpyArray<1, Singleband<IND> >& radii,
                         IND x, IND y, IND c, NumpyArray<3, Multiband<T> >& predictions,
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
    //if (nn2<8) {
    //    wa = 0;
    //}
    //std::cout<<"in new features, nr= "<<nr<<" , nc = "<<nclasses<<" , x= "<<x<<" , y= "<<y<<std::endl;
    for (int ir=0; ir<nr; ++ir) {
        //std::cout<<"ir = "<<ir<<", rad = "<<radii[ir]<<std::endl;
        IND xminus = x - radii[ir];
        IND xplus = x + radii[ir];
        IND yminus = y - radii[ir];
        IND yplus = y + radii[ir];
        //std::cout<<"bla1"<<std::endl;
        
        if (x<radii[ir]) {
            //std::cout<<"bla1.1"<<" , x="<<x<<" , radii[ir]="<< radii[ir]<<std::endl;
            neighbors[ir*nn + 0] = 1./nclasses;
            neighbors[ir*nn + 1] = 1./nclasses;
            neighbors[ir*nn + 2] = 1./nclasses;
            if (wa) {
                
                neighbors[ir*nn + nn2 + 0] = 1./nclasses;
                neighbors[ir*nn + nn2 + 1] = 1./nclasses;
                neighbors[ir*nn + nn2 +2] = 1./nclasses;
            }
        } else {
            //std::cout<<"bla1.2"<<std::endl;
            //std::cout<<"bla1.2"<<" , x="<<x<<" , radii[ir]="<< radii[ir]<<std::endl;
            if (y<radii[ir]) {
                //std::cout<<"bla1.3"<<" , y="<<y<<" , radii[ir]="<< radii[ir]<<std::endl;
                neighbors[ir*nn + 0] = 1./nclasses;
                if (wa) neighbors[ir*nn+nn2+0] = 1./nclasses;
            } else {
                //std::cout<<"bla1.4"<<" , y="<<y<<" , radii[ir]="<< radii[ir]<<std::endl;
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
        //std::cout<<"bla2"<<std::endl;
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
            //std::cout<<"bla1.5"<<" , x="<<x<<" , radii[ir]="<< radii[ir]<<std::endl;
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
                //std::cout<<"bla1.6"<<" , y="<<y<<" , radii[ir]="<< radii[ir]<<std::endl;
                neighbors[ir*nn + 5] = 1./nclasses;
                if (wa) neighbors[ir*nn+nn2+5] = 1./nclasses;
            } else {
                //std::cout<<"bla1.7"<<" , y="<<y<<" , radii[ir]="<< radii[ir]<<std::endl;
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


        
template <class IND, class T>
T average_pred(IND x, IND y, IND c, int nav, NumpyArray<3, Multiband<T> >& predictions)
{
    //this function computes the average of predictions in nav_x_nav neighborhoods
    //
    T sum = 0;
    int n = 0;
    //std::cout<<"x= "<<x<<" , y= "<<y<<std::endl;
    int nclasses = predictions.shape()[2];
    int nx = predictions.shape()[0];
    int ny = predictions.shape()[1];
    int lim = (nav-1)/2;
    //std::cout<<"lim= "<<lim<<std::endl;
    if (x<lim) {
        //std::cout<<"bla1"<<std::endl;
        return 1./nclasses;
    }
    if (y<lim) {
        //std::cout<<"bla2"<<std::endl;
        return 1./nclasses;
    }
    if (x>=nx-lim) {
        //std::cout<<"bla3"<<std::endl;
        return 1./nclasses;
    }
    if (y>=ny-lim) {
        //std::cout<<"bla4"<<std::endl;
        return 1./nclasses;
    }
    
    for (IND ix = x-lim; ix<x+lim+1; ++ix) {
        for (IND iy = y-lim; iy<y+lim+1; ++iy) {
            //if (x==1 && y==1) {
            //    std::cout<<"ix="<<ix<<" , iy="<<iy<<" , pred="<< predictions(ix, iy, c)<<std::endl;
            //}
            sum+=predictions(ix, iy, c);
            n++;
        }
    }
    return sum/n;
}
*/    
    
template <class IND, class T>
void starContext3D(NumpyArray<1, Singleband<IND> >& radii, 
                   NumpyArray<1, Singleband<IND> >& fullshape,
                   NumpyArray<1, Singleband<IND> >& selections,
                   NumpyArray<2, Singleband<T> >& predictions, 
                   NumpyArray<2, Singleband<T> >& res)
{

    uint npoints = predictions.shape()[0];
    uint nclasses = predictions.shape()[1];

    //for now, only do the predictions for nclasses at each point, no averages
    int nnew = radii.size()*nclasses*26;
    std::cout<<"results shape: "<<res.shape()<<std::endl;
    if (selections.size()>2) {
        //predicting only selected points, probably in training
        int ns = selections.size();
        for (int is=0; is<ns; ++is) {
            //std::cout<<"selection index: "<<is<<std::endl;
            IND ind = selections[is];
            std::vector<IND> fullindex(3, 0);
            unravel_index(ind, fullshape, fullindex);
            //IND temp = ravel_index(fullindex[0], fullindex[1], fullindex[2], fullshape);
            //if (temp!=ind){
            //    std::cout<<"difference b/w ravel and unravel "<< temp << "  "<< ind<< std::endl;
            //} else {
            //    std::cout<<"all good: "<< temp <<"  "<< ind <<std::endl;
            //}
            
            //std::vector<IND> neighbors(nnew/nclasses, std::numeric_limits<IND>::max());
            std::vector<IND> neighbors;
            neighbor_indices(radii, fullindex, fullshape, neighbors);
            int icurrent = 0;
            int ifeat = 0;
            typename std::vector<IND>::iterator it;
            for (it=neighbors.begin(); it!=neighbors.end(); ++it) {
                if ((*it)==std::numeric_limits<IND>::max()) {
                    //std::cout<<"out of block"<<std::endl;
                    //out of the block, assign uniform probability
                    for (int ifeat=0; ifeat<nclasses; ++ifeat, ++icurrent){
                        //std::cout<<icurrent<<std::endl;
                        res[is*nnew + icurrent] = 1./nclasses;
                    }
                } else {
                    for (int ifeat=0; ifeat<nclasses; ++ifeat, ++icurrent){
                        res[is*nnew + icurrent] = predictions[(*it)*nclasses+ifeat];
                    }
                }
            }
            
            
        }
        
    } else {
        
        //predicting everything
        int nx = fullshape.shape()[0];
        int ny = fullshape.shape()[1];
        int nz = fullshape.shape()[2];
        for (IND z=0; z<nz; ++z) {
            for (IND y=0; y<ny; ++y){
                for (IND x=0; x<nx; ++x) {
                    std::vector<IND> neighbors;
                    std::vector<IND> fullindex;
                    fullindex.push_back(x);
                    fullindex.push_back(y);
                    fullindex.push_back(z);
                    neighbor_indices(radii, fullindex, fullshape, neighbors);
                    IND flatindex = ravel_index(x, y, z, fullshape);
                    int icurrent = 0;
                    int ifeature = 0;
                    typename std::vector<IND>::iterator it;
                    for (it=neighbors.begin(); it!=neighbors.end(); ++it) {
                        if ((*it)==std::numeric_limits<IND>::max()) {
                            //std::cout<<"out of block"<<std::endl;
                            //out of the block, assign uniform probability
                            for (int ifeat=0; ifeat<nclasses; ++ifeat, ++icurrent){
                                //std::cout<<icurrent<<std::endl;
                                res[flatindex*nnew + icurrent] = 1./nclasses;
                            }
                        } else {
                            for (int ifeat=0; ifeat<nclasses; ++ifeat, ++icurrent){
                                res[flatindex*nnew + icurrent] = predictions[(*it)*nclasses+ifeat];
                            }
                        }                    
                    }
                }
            }
        }
    }           
    return;
}
/*                                           
template <class IND, class T>
void starContext2Dmulti(NumpyArray<1, Singleband<IND> >& radii,
                   NumpyArray<3, Multiband<T> >& predictions,
                   NumpyArray<3, Multiband<T> >& res)
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
                //std::cout<<x<<" "<<y<<std::endl;
                std::vector<T> neighbors(nnewfeatures);
                //std::vector<T> neighbors_average(radii.size()*8);
                //new_features_simple(radii, x, y, c, predictions, neighbors_simple);
                //std::cout<<"x="<<x<<", y="<<y<<", neighbors size: "<<neighbors.size()<<std::endl;
                new_features(radii, x, y, c, predictions, neighbors);
                for (IND ii=0; ii<nnewfeatures; ++ii){
                    //std::cout<<"index: "<<c*nnewfeatures+ii<<" , ii: "<<ii<<" , neighbors[ii]: "<<neighbors[ii]<<std::endl;
                    res(x, y, c*nnewfeatures + ii) = neighbors[ii];
                    
                    //res(x, y, c*nnewfeatures+neighbors_simple.size()+ii) = neighbors_average[ii];
                }
                //std::cout<<"res filled"<<std::endl;
                
            }
        }
    }
    return;
}
*/

template <class IND, class T>
void starContext2D(NumpyArray<1, Singleband<IND> >& radii, 
                                       NumpyArray<1, Singleband<IND> >& fullshape,
                                       NumpyArray<1, Singleband<IND> >& selections,
                                       NumpyArray<2, Singleband<T> >& predictions, 
                                       NumpyArray<2, Singleband<T> >& res)
{
    uint npoints = predictions.shape()[0];
    uint nclasses = predictions.shape()[1];

    //for now, only do the predictions for nclasses at each point, no averages
    int nnew = radii.size()*nclasses*8;
    std::cout<<"results shape: "<<res.shape()<<std::endl;
    if (selections.size()>2) {
        //predicting only selected points, probably in training
        int ns = selections.size();
        for (int is=0; is<ns; ++is) {
            //std::cout<<"selection index: "<<is<<std::endl;
            IND ind = selections[is];
            std::vector<IND> fullindex(3, 0);
            unravel_index(ind, fullshape, fullindex);
            //IND temp = ravel_index(fullindex[0], fullindex[1], fullindex[2], fullshape);
            //if (temp!=ind){
            //    std::cout<<"difference b/w ravel and unravel "<< temp << "  "<< ind<< std::endl;
            //} else {
            //    std::cout<<"all good: "<< temp <<"  "<< ind <<std::endl;
            //}
            
            //std::vector<IND> neighbors(nnew/nclasses, std::numeric_limits<IND>::max());
            std::vector<IND> neighbors;
            neighbor_indices_2d(radii, fullindex, fullshape, neighbors);
            int icurrent = 0;
            int ifeat = 0;
            typename std::vector<IND>::iterator it;
            for (it=neighbors.begin(); it!=neighbors.end(); ++it) {
                if ((*it)==std::numeric_limits<IND>::max()) {
                    //std::cout<<"out of block"<<std::endl;
                    //out of the block, assign uniform probability
                    for (int ifeat=0; ifeat<nclasses; ++ifeat, ++icurrent){
                        //std::cout<<icurrent<<std::endl;
                        res[is*nnew + icurrent] = 1./nclasses;
                    }
                } else {
                    for (int ifeat=0; ifeat<nclasses; ++ifeat, ++icurrent){
                        res[is*nnew + icurrent] = predictions[(*it)*nclasses+ifeat];
                    }
                }
            }
            
            
        }
        
    } else {
        
        //predicting everything
        int nx = fullshape.shape()[0];
        int ny = fullshape.shape()[1];
        //int nz = fullshape.shape()[2];
        //for (IND z=0; z<nz; ++z) {
        for (IND y=0; y<ny; ++y){
            for (IND x=0; x<nx; ++x) {
                std::vector<IND> neighbors;
                std::vector<IND> fullindex;
                fullindex.push_back(x);
                fullindex.push_back(y);
                //fullindex.push_back(z);
                neighbor_indices_2d(radii, fullindex, fullshape, neighbors);
                IND flatindex = ravel_index_2d(x, y,fullshape);
                int icurrent = 0;
                int ifeature = 0;
                typename std::vector<IND>::iterator it;
                for (it=neighbors.begin(); it!=neighbors.end(); ++it) {
                    if ((*it)==std::numeric_limits<IND>::max()) {
                        //std::cout<<"out of block"<<std::endl;
                        //out of the block, assign uniform probability
                        for (int ifeat=0; ifeat<nclasses; ++ifeat, ++icurrent){
                            //std::cout<<icurrent<<std::endl;
                            res[flatindex*nnew + icurrent] = 1./nclasses;
                        }
                    } else {
                        for (int ifeat=0; ifeat<nclasses; ++ifeat, ++icurrent){
                            res[flatindex*nnew + icurrent] = predictions[(*it)*nclasses+ifeat];
                        }
                    }                    
                }
            }
        }
        //}
    }           
    
    
    return;
}



/*

template <class SrcIterator, class SrcAccessor,class SrcShape,
          class DestIterator, class DestAccessor>
int simpleContext(SrcIterator s_Iter, SrcShape srcShape, SrcAccessor sa,
                         DestIterator d_Iter, DestAccessor da)
{
    // for the moment, just copy the predictions to features
    int nobs = srcShape[0], nlabels = srcShape[1];
    printf("C++, the input shape: %d, %d\n", nobs, nlabels);
    
    int iobs, ilabel, ifeature;       
    
    DestIterator ds = d_Iter;
    SrcIterator ss = s_Iter;
    
    for (iobs=0; iobs<nobs; ++iobs, ++ss.dim0(), ++ds.dim0()) {
        //printf("iobs = %d \n", iobs);
        ifeature=0;
        for (ilabel=0; ilabel<nlabels; ++ilabel, ++ss.dim1(), ++ds.dim1()) {
            //printf("ilabel = %d\n", ilabel);
            //ds.dim0() += ifeature;
            //da(ds) = sa(ss);
            std::cout<<"source: "<<sa(ss)<<std::endl;
            da.set(sa(ss), ds);
            ifeature++;
            //printf("ifeatures = %d\n", ifeature);
        }
    }
    return 1;
}


template <class SrcIterator, class SrcAccessor,class SrcShape,
          class DestIterator, class DestAccessor>
int simpleContext(triple<SrcIterator, SrcShape, SrcAccessor> src,
                         pair<DestIterator, DestAccessor> dest)
{
    return simpleContext(src.first, src.second, src.third, dest.first, dest.second);
    //SrcIterator s_Iter = src.first;
    //SrcShape srcShape = src.second;
    //SrcAccessor sa = src.third;
    //DestIterator d_Iter = dest.first;
    //DestAccessor da = dest.second;
    
    
}

*/ 

#endif
