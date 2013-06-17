import numpy as np
from scipy import ndimage
import sklearn
from sklearn import preprocessing
from sklearn.metrics import pairwise
import itertools
try:
    import gurobipy as gu
except:
    pass

import h5py, cPickle

#!/usr/bin/python

# Copyright 2013, Gurobi Optimization, Inc.

# This example formulates and solves the following simple QP model:
#
#    minimize    x + y + x^2 + x*y + y^2 + y*z + z^2
#    subject to  x + 2 y + 3 z >= 4
#                x +   y       >= 1
#
# The example illustrates the use of dense matrices to store A and Q
# (and dense vectors for the other relevant data).  We don't recommend
# that you use dense matrices, but this example may be helpful if you
# already have your data in this format.

import sys
from scipy import spatial


class RegressorGurobi(object):
    

    def __init__(self, C=1, epsilon=0.1, penalty="l2",regularization="l2",pos_constr=False):
        """
            penalty : "l1" or "l2" penalty
            
        """
        
        self.penalty=penalty
        self._C = C
        self._epsilon = epsilon
        self.regularization=regularization
        
        self.pos_constr=pos_constr
    
    def get_Xhat(self,X):
        return np.hstack( [X,np.ones((X.shape[0],1))])
    
    def predictUnfiltered(self,X):
        
        oldShape = X.shape
        result = np.dot(self.get_Xhat(X.reshape((-1, X.shape[-1]))),self.w).reshape(X.shape[:-1])
        return result

    def fit(self,X,Yl,tags = None, boxConstraints = None):

        
        #format for box constraints: [(boxvalue, features)]
        
        
        self.Nf = X.shape[1]
        X_hat=self.get_Xhat(X)

        
        model=gu.Model()
        
        model.setParam("Threads",2 )
        #print "creating vars ... ",
        #create the variables
        u_vars1=[model.addVar(name="u^+_%d"%i,lb=0,vtype=gu.GRB.CONTINUOUS) for i in range(X.shape[0])]
        u_vars2=[model.addVar(name="u^-_%d"%i,lb=0,vtype=gu.GRB.CONTINUOUS) for i in range(X.shape[0])]
        w_vars=[model.addVar(name="w_%d"%i,lb=-gu.GRB.INFINITY,vtype=gu.GRB.CONTINUOUS) for i in range(self.Nf+1)]
        
         
        model.update()
        print "done "
        
        #print "setting penalty objective %s ..."%self.penalty,
        obj=None
        if self.penalty=="l1":
            obj=self._C * (gu.quicksum([u for u in u_vars1 ])+gu.quicksum([u for u in u_vars2 ]))
        elif self.penalty=="l2":
            obj=self._C * (gu.quicksum([u*u for u in u_vars1 ])+gu.quicksum([u*u for u in u_vars2 ]))
        else:
            print  "penalty term not know !"
            raise RuntimeError
        
        
            
        obj += 0.5 * gu.quicksum(w * w for w in w_vars[:-1] )

        model.setObjective(obj)


        print "done"
        #print "objective = ", model.getObjective()
        
        ### add constraint for the variables
        print "adding constraint penalty"
        if tags:
            for i in range(sum(tags)):
                #logme("%.2f"%(i/float(X_hat.shape[0])*100.0))
                constr=gu.quicksum([float(X_hat[i,j])*w_vars[j] for j in range(self.Nf+1)]) - u_vars1[i]<=float(Yl[i]) + self._epsilon
                model.addConstr(constr )
            for i in range(tags[0]):
                constr=gu.quicksum([-(float(X_hat[i,j])*w_vars[j])  for j in range(self.Nf+1)]) - u_vars2[i]<=-float(Yl[i]) + self._epsilon
                model.addConstr(constr)        
        else:
            for i in range(X.shape[0]):
		    constr=gu.quicksum([float(X_hat[i,j])*w_vars[j] for j in range(self.Nf+1)]) - u_vars1[i]<=float(Yl[i]) + self._epsilon
		    model.addConstr(constr )
		    constr=gu.quicksum([-(float(X_hat[i,j])*w_vars[j])  for j in range(self.Nf+1)]) - u_vars2[i]<=-float(Yl[i]) + self._epsilon
		    model.addConstr(constr)        

        model.update()
        model.setParam('OutputFlag', False) 
        #model.write("test.lp")
        model.optimize()
        
        #self.w=np.array([w.x for w in w_vars]).reshape(-1,1)
        ##print model.status==gu.GRB.status.OPTIMAL
        ##print "Obj: ",model.getObjective().getValue()

        self.w=np.array([w.x for w in w_vars]).reshape(-1,1)


        if boxConstraints is not None:
            numConstraintVariables = [features.shape[0] for (value, features) in boxConstraints]
            diffopminus = [model.addVar(name="diff-_%d"%i,lb=0,vtype=gu.GRB.CONTINUOUS) for i in
                            range(len(boxConstraints))]
            diffopplus = [model.addVar(name="diff+_%d"%i,lb=0,vtype=gu.GRB.CONTINUOUS) for i in
                            range(len(boxConstraints))]
            z_vars = []
            b_vars = []
            isForegroundIndicators = []

            for i in range(len(boxConstraints)):
                value, features = boxConstraints[i]
                assert features.shape[1] == self.Nf
                res = self.predict(features)
                res[np.where(res >0)] = 1
                isForegroundIndicators.append(res)

                z_vars.append([model.addVar(name = "z_{}_{}".format(i, j), vtype = gu.GRB.CONTINUOUS) for j in
                      range(sum(numConstraintVariables)) ])
                b_vars.append([model.addVar(name = "b_{}_{}".format(i, j), lb = 0, vtype = gu.GRB.CONTINUOUS) for j in
                      range(sum(numConstraintVariables)) ])

            model.update()

            for i, b_i,fore_i, z_i, boxConstraint in zip(range(len(boxConstraints)), b_vars, isForegroundIndicators, z_vars, boxConstraints):
                value, features = boxConstraint
                for b, fore, z, feature in zip(b_i, fore_i, z_i, features):

                    multconstr = gu.quicksum([float(feature[j]) * w_vars[j] for j in range(self.Nf)]) + w_vars[-1] <= z
                    model.addConstr(multconstr)
                    multconstr = -gu.quicksum([float(feature[j]) * w_vars[j] for j in range(self.Nf)]) - w_vars[-1] <= z
                    model.addConstr(multconstr)
                
                    active = float(1 - fore)

                    activeconstr1 = active >=  b
                    model.addConstr(activeconstr1)
                    activeconstr3 = 1 - active >=  gu.quicksum([float(feature[j])*w_vars[j] for j in range(self.Nf)])+\
                        w_vars[-1] + b
                    model.addConstr(activeconstr3)

                
                condensedFeatures = np.sum(features, axis = 0)
                boxconstrmax = diffopminus[i] >= 0.5 * (gu.quicksum([float(condensedFeatures[j])*w_vars[j] for j in
                                                                     range(self.Nf)])+float(features.shape[0]) \
                * w_vars[-1]) + 0.5 * gu.quicksum([z for z in z_i])  - float(value) 
                
                model.addConstr(boxconstrmax)


                boxconstrmin = diffopplus[i] >= float(value) - gu.quicksum([float(condensedFeatures[j])*w_vars[j] for
                            j in range(self.Nf)] ) - float(features.shape[0]) * w_vars[-1] - gu.quicksum([b for b in b_i]) 
                

                model.addConstr(boxconstrmin)

                obj += self._C * float(1./features.shape[0]) * diffopplus[i] * diffopplus[i]
                obj += self._C * float(1./features.shape[0]) * diffopminus[i] * diffopminus[i]

            model.setObjective(obj)
        
            model.update()    
            model.optimize()
            #import sitecustomize
            #sitecustomize.debug_trace()

            self.w=np.array([w.x for w in w_vars]).reshape(-1,1)

        return self  

    def predict(self, X):
        
        oldShape = X.shape
        result = np.dot(self.get_Xhat(X.reshape((-1, X.shape[-1]))),self.w).reshape(X.shape[:-1])
        return result

        



class SVR(object):


    options = [
        {"optimization" : "rf-sklearn" ,"gui":["default","rf"], "req":["sklearn"]},
        {"optimization" : "svr-sklearn", "kernel" : "rbf","gui":["default","svr"], "req":["sklearn"]},
        {"optimization" : "svrBoxed-gurobi", "gui":["default", "svr"], "req":["gurobipy"]},
        {"optimization" : "svr-gurobi", "gui":["default", "svr"], "req":["gurobipy"]}
        #{"optimization" : "svr-gurobi", "gui":["default", "svr"], "req":["dummy"]}
    #{"optimization" : "svr", "kernel" : "linear","gui":["default","svr"]},
    #{"optimization" : "svr", "kernel" : "poly","gui":["default","svr"]},
    #{"optimization" : "svr", "kernel" : "sigmoid","gui":["default","svr"]},
    #{"optimization" : "quadratic", "kernel" : "linear","gui":["default","svr"]},
    #{"optimization" : "quadratic", "kernel" : "rbf","gui":["default","svr"]}
    #{"optimization" : "smo", "kernel" : "linear"},
    #{"optimization" : "smo", "kernel" : "gaussian"}
    ]


    def __init__(self, C = 1, epsilon = 0.001, limitDensity = True, optimization = "quadratic", kernel ="linear" ,\
                  ntrees=10, maxdepth=None, #RF parameters, maxdepth=None means grows untill purity
                 **kwargs
                 ):
        """
        underMult : penalty-multiplier for underestimating density
        overMult : penalty-multiplier for overestimating the density
        """
        self.DENSITYBOUND=limitDensity
        #self.upperBounds = [None, underMult, overMult]
        self._epsilon = epsilon
        self._C = C

        self._trained = False
        self._kernel = kernel
        self._optimization = optimization
        
        #RF parameters:
        self._ntrees=ntrees
        self._maxdepth=maxdepth
        
    @classmethod
    def load(self, cachePath, targetname):
        f = h5py.File(cachePath, 'r')
        dataset = f[targetname]
        obj = cPickle.loads(dataset[0])
        f.close()
        return obj

    def prepareData(self, oldImg, oldDot, sigma, smooth, normalize):

        dot = np.copy(oldDot.reshape(oldImg.shape[:-1]))
        backupindices = np.where(dot == 2)
        dot[backupindices] = 0
        dot[np.where(dot == 1)] = 255

        
        if len(sigma) == 1 or len(sigma) < len(dot.shape):
            sigma = sigma[0]
        if smooth:
            dot = ndimage.filters.gaussian_filter(dot.astype(np.float32), sigma) #TODO: use it later, but this
            dot[backupindices] = 0

        #is terrible for debugging
        nindices = np.ravel_multi_index(backupindices, dot.shape) #TODO: CHANGE BACK
        dot = dot.reshape(-1)
        img = np.copy(oldImg.reshape((-1,oldImg.shape[-1])))
        if normalize:
            img = sklearn.preprocessing.normalize(img, axis=0)
        pindices = np.where(dot > 0.0001)[0]
        #pindices = pindices[:250]
        lindices = None
        if self.DENSITYBOUND:
            lindices = np.concatenate((nindices, pindices))
        else:
            lindices = nindices

        #lindices = np.concatenate((pindices, nindices))
        numVariables = len(pindices) + len(lindices) 

        mapping = np.concatenate((pindices, lindices))

        tags = [len(pindices), len(lindices)]
        #print dot
        self.dot = dot
        self.img = img

        return img, dot, mapping, tags
   
    def fit(self, img, dot, sigma, smooth = True, normalize = False):

        newImg, newDot, mapping, tags = \
        self.prepareData(img, dot, sigma, smooth, normalize)
        self.fitPrepared(newImg[mapping,:], newDot[mapping], tags)

    def fitPrepared(self, img, dot, tags, boxConstraints = []):
        

        numFeatures = img.shape[-1]
        numVariables = sum(img.shape[:-1])
        if numVariables == 0:
            return False
        success = False
        #tags.append(len(boxConstraints))

        if self._optimization == "rf-sklearn":
            from sklearn.ensemble import RandomForestRegressor as RFR
            
            regressor = RFR(n_estimators=self._ntrees,max_depth=self._maxdepth)
            print "Trining the random forest ", regressor
            regressor.fit(img, dot)

            #C = np.array([self.upperBounds[tag] for tag in tags], dtype = np.float)
            #svr.fit(img, dot, tags, sample_weight = C) 
            #svr.fit(img, dot) 
            #print svr.predict(img)
            #print svr.dual_coef_
            self._regressor = regressor
            success = True

        elif self._optimization == "svr-sklearn":
            from sklearn.svm import SVR
            regressor = SVR(kernel = self._kernel, C = self._C)
            regressor.fit(img, dot)
            self._regressor = regressor
            success = True

        elif self._optimization == "svrBoxed-gurobi":
            regressor = RegressorGurobi(C = self._C, epsilon = self._epsilon)
            regressor.fit(img, dot, tags, boxConstraints)
            self._regressor = regressor
            success = True
        
        elif self._optimization == "svr-gurobi":
            regressor = RegressorGurobi(C = self._C, epsilon = self._epsilon)
            regressor.fit(img, dot, boxConstraints)
            self._regressor = regressor
            success = True
            

        if success:
            self.trained = True
        return success
    
    def predict(self, oldImage, normalize = False):
        if not self.trained:
            return np.zeros(oldImage.shape[:-1])
        oldShape = oldImage.shape
        image = np.copy(oldImage.reshape((-1, oldImage.shape[-1])))
        if normalize:
            image = sklearn.preprocessing.normalize(image, axis=0)
        if self._optimization == "rf-sklearn":
            res = self._regressor.predict(image)
        elif self._optimization == "svr-sklearn":
            res = self._regressor.predict(image)
        elif self._optimization == "svrBoxed-gurobi":
            res = self._regressor.predict(image)

        #res = np.zeros(oldShape[:-1])
        res = res.view(np.ndarray)
        res[np.where(res < 0)] = 0
        return res.reshape(oldShape[:-1])

    def writeHDF5(self, cachePath, targetname):
        f = h5py.File(cachePath, 'w')
        str_type = h5py.special_dtype(vlen = str)
        dataset = f.create_dataset(targetname, shape = (1,), dtype = str_type)
        dataset[0] = cPickle.dumps(self)
        f.close()





if __name__ == "__main__":

    np.set_printoptions(precision=4)
    np.set_printoptions(threshold = 'nan')
    img = np.load("img.npy")
    dot = np.load("dot.npy")
    #img = img[...,[2]]
    #img = img[..., None]
    
    DENSITYBOUND=False
    pMult = 100 #This is the penalty-multiplier for underestimating the density
    lMult = 100 #This is the penalty-multiplier for overestimating the density

    #shortExample
    limits = [50, 200]
    img = img[limits[0]:limits[1],limits[0]:limits[1],:]
    dot = dot[limits[0]:limits[1],limits[0]:limits[1]]

   #ToyExample
    img = np.ones((9,9,2),dtype=np.float32)
    dot = np.zeros((9,9))
    img = 1 * img
    img[:,:,1] = np.random.rand(*img.shape[:-1])
    img[0,0] = 3
    img[1,1] = 3
    img[3:6,3:6] = 50
    dot[4,4] = 1
    dot[5,5] = 1
    dot[0,0] = 2
    dot[1,1] = 2

    backup_image = np.copy(img)
    Counter = SVR(pMult, lMult, DENSITYBOUND, kernel = "linear", optimization =
                 "svr")
    sigma = [0]
    testimg, testdot, testmapping, testtags = Counter.prepareData(img, dot,
                                                                  sigma,
                                                                  normalize =
                                                                  False, smooth
                                                                  = True
                                                                  )
    #print "blub", testimg.shape
    #print testimg
    #print testdot, np.sum(testdot)
    boxConstraints = []
    #boxConstraints = [(12, img[:,:,:])]
    #boxConstraints = [(3, img[0:30,0:30,:])]
    #boxConstraints.reshape((-1, boxConstraints.shape[-1]))
    success = Counter.fitPrepared(testimg[testmapping,:], testdot[testmapping], testtags, epsilon = 0.000,
                                  boxConstraints = boxConstraints)
    #success = Counter.fitPrepared(testimg[indices,:], testdot[indices], testtags[:len(indices)], epsilon = 0.000)
    #print Counter.w, Counter.
    print "learning finished"

    #conversion step
    #Q = kernelize(B, method = "gaussian")
    ##Q = B * B.transpose()
    #tags = np.zeros(numVariables,dtype=np.int8)
    #tags[0:len(pindices)] = 1
    #tags[len(pindices):] = -1
    #c = dot[allIndices] * (-tags)+ epsilon
    #upperBounds = [None, pMult, lMult]
    #success,solution = optimize(tags,Q,c,upperBounds)
    ## Put model data into dense matrices
    #print Counter.b, Counter.w
    newdot = Counter.predict(backup_image, normalize = False)

    print "prediction"
    #print img
    #print newdot
    print "sum", np.sum(newdot) / 1
    try: 
        import matplotlib.pyplot as plt
        import matplotlib
        fig = plt.figure()
        fig.add_subplot(1,3,1)
        plt.imshow(testimg[...,0].astype('uint8').reshape(backup_image.shape[:-1]), cmap=matplotlib.cm.gray)
        fig.add_subplot(1,3,2)
        plt.imshow(newdot.reshape(backup_image.shape[:-1]), cmap=matplotlib.cm.gray)
        fig.add_subplot(1,3,3)
        plt.imshow(testdot.reshape(backup_image.shape[:-1]), cmap=matplotlib.cm.gray)
        plt.show()
    except:
        pass
    #print Counter.w, Counter.b
    #debug_trace()
    #
    #c = [1, 1, 0]
    #Q = [[1, 1, 0], [0, 1, 1], [0, 0, 1]]
    #A = [[1, 2, 3], [1, 1, 0]]
    #sense = [GRB.GREATER_EQUAL, GRB.GREATER_EQUAL]
    #rhs = [4, 1]
    #lb = [0, 0, 0]
    #ub = [GRB.INFINITY, GRB.INFINITY, GRB.INFINITY]
    #vtype = [GRB.CONTINUOUS, GRB.CONTINUOUS, GRB.CONTINUOUS]
    #sol = [0]*3
    #
    ## Optimize
    #
    #success = dense_optimize(2, 3, c, Q, A, sense, rhs, lb, ub, vtype, sol)
    #
    #if success:
    #  print 'x: ', sol[0], 'y: ', sol[1], 'z: ', sol[2]
    #for i in range(numVariables):
    #    m.addVar()


