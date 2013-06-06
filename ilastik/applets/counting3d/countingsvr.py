import numpy as np
from scipy import ndimage
import sklearn
from sklearn import preprocessing
from sklearn.metrics import pairwise
import itertools

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
import gurobipy
from scipy import spatial


def kernelize(B, dot, tags,epsilon, kernel, boxConstraints):
    coeff = tags[:,None] * tags[None,:]
    if kernel == "linear":
        Q = np.multiply(coeff,(B * B.transpose()))
        #debug_trace()
        c = dot * (-tags) + epsilon
        return Q, c
    elif kernel == "gaussian":
        gamma = 10000
        #debug_trace()
        Q = spatial.distance.pdist(B, metric="sqeuclidean")
        Q = -gamma * Q
        Q = np.exp(spatial.distance.squareform(Q))
        Q = np.multiply(coeff,Q)
        return Q

def createKernel(B, dot, tags, epsilon, kernel, boxConstraints):
    n_jobs = 1
    num_features = B.shape[1]
    #coeffUpperLeft = tags[:,None] * tags[None,:]
    #if kernel == "linear":
    numTrainingExamples = B.shape[0]
    QUpperRight = np.ndarray((numTrainingExamples, len(boxConstraints)))
    QLowerRight = np.ndarray((len(boxConstraints), len(boxConstraints)))
    expandedTags = np.concatenate((np.ones(tags[0]), -1 * np.ones(np.sum(tags[1:]))))
    print "beep"
    if kernel == "linear":
        def _evaluate(x,y):
            return np.matrix(x) * np.matrix(y).transpose()

    elif kernel == "rbf":
        def _evaluate(x,y):
            metric = "euclidean"
            tmp = pairwise.pairwise_distances(x, y, metric = metric, n_jobs = n_jobs)
            tmp = np.exp(-(tmp**2) / (num_features * 1000))
            return tmp

    boxValues = []
    for i, constraint in enumerate(boxConstraints):
        val,features = constraint
        boxValues.append(val)
        features = features.reshape(-1, features.shape[-1])
        tmp = _evaluate(B, features)
        QUpperRight[:,i] = np.sum(tmp, axis = 1).flatten()

        #boxMatrix[i] = np.sum(features, axis = 0)
    #boxMatrix = np.matrix(boxMatrix)
    for i, j in zip(range(len(boxConstraints)), range(len(boxConstraints))):
        val1, features1 = boxConstraints[i]
        val2, features2 = boxConstraints[j]
        features1 = features1.reshape(-1, features1.shape[-1])
        features2 = features2.reshape(-1, features2.shape[-1])
        tmp = _evaluate(features1, features2)
        QLowerRight[i,j] = np.sum(tmp).flatten()

         
    QLowerLeft = QUpperRight.transpose()
    QUpperLeft = _evaluate(B,B) 
    QUpper     = np.concatenate((QUpperLeft, QUpperRight), axis = 1)
    QLower     = np.concatenate((QLowerLeft, QLowerRight), axis = 1)
    Q          = np.concatenate((QUpper, QLower), axis = 0)

    coeff      = expandedTags[:,None] * expandedTags[None, :]
    Q          = np.multiply(coeff, Q)

    #QUpperLeft = np.multiply(coeff,(B * B.transpose()))
    #QLowerLeft = B * boxConstraints.transpose()
    #QLowerRight= boxConstraints * B.transpose()
    #QUpperRight= -boxConstraints*boxConstraints.transpose()
    print "boop"
    
    c = np.concatenate((dot, boxValues))  * (-expandedTags) + epsilon
    return Q,c
    



def optimizepossdef(tags, B, c, upperBounds, boxConstraints = None):
    model = gurobipy.Model()
    expandedTags = np.concatenate((np.ones(tags[0]), -1 * np.ones(np.sum(tags[1:]))))
    B = np.multiply(expandedTags[:,None], B) 

    for j in range(tags[0]):
        model.addVar(lb=0., ub=float(upperBounds[1]), vtype=gurobipy.GRB.CONTINUOUS)
    
    for j in range(sum(tags[1:])):
        model.addVar(lb=0., ub=float(upperBounds[-1]), vtype=gurobipy.GRB.CONTINUOUS)

    model.update()
    vars = model.getVars()

    expr = gurobipy.LinExpr()
    for j in range(sum(tags)):
        expr += expandedTags[j]*vars[j]

    model.addConstr(expr, gurobipy.GRB.EQUAL, 0)
    print "ping"
    # Populate objective
    y = [None for i in range(B.shape[1])]
    for i in range(B.shape[1]):
        y[i] = model.addVar(name = 'y_%s' % (i))
    model.update()

    for i in range(B.shape[1]):
        expr = gurobipy.LinExpr()
        #for j in range(B.shape[0]):
        #    expr += B[j,i] * vars[j]
        expr.addTerms(B[:,i], vars)
        model.addConstr(expr, gurobipy.GRB.EQUAL, y[i])


    obj = gurobipy.QuadExpr()
    #vararray = zip(*itertools.product(vars,vars))
    #obj.addTerms(0.5 * Q.view(np.ndarray).flatten(),vararray[0], vararray[1])
    #debug_trace()
    obj.addTerms(0.5 * np.ones(len(y)), y, y)
    obj.addTerms(c, vars)
    model.setObjective(obj,gurobipy.GRB.MINIMIZE)
    print "pong"
  # Write model to a file
    model.update()
    model.write('dense.lp')
    print "blub"
  # Solve
    model.optimize()
    print "blob"
    solution = np.ndarray((expandedTags.shape[0]))
    if model.status == gurobipy.GRB.OPTIMAL:
        for i in range(solution.shape[0]):
            solution[i] = vars[i].x
        return True, solution
    else:
        return False

def optimize(tags, Q, c, upperBounds):

    model = gurobipy.Model()

    expandedTags = np.concatenate((np.ones(tags[0]), -1 * np.ones(np.sum(tags[1:]))))
    # Add variables to model
    for j in range(tags[0]):
        model.addVar(lb=0., ub=float(upperBounds[1]), vtype=gurobipy.GRB.CONTINUOUS)

    for j in range(sum(tags[1:])):
        model.addVar(lb=0., ub=float(upperBounds[-1]), vtype=gurobipy.GRB.CONTINUOUS)

    model.update()
    vars = model.getVars()

    expr = gurobipy.LinExpr()
    for j in range(sum(tags)):
        expr += expandedTags[j]*vars[j]

    model.addConstr(expr, gurobipy.GRB.EQUAL, 0)
    print "ping"
    # Populate objective
    #y_vars = {}
    #for i in range(B.shape[1]):
    #    y[i] = model.addVar(name = 'y_%s' % (i))

    
    obj = gurobipy.QuadExpr()
    vararray = zip(*itertools.product(vars,vars))
    obj.addTerms(0.5 * Q.view(np.ndarray).flatten(),vararray[0], vararray[1])
    #for i in range(Q.shape[0]):
    #    for j in range(Q.shape[1]):
    #        if Q[i,j] != 0:
    #            obj += Q[i,j]*vars[i]*vars[j]
    


    print "ping"
    obj.addTerms(c, vars)
    model.setObjective(obj,gurobipy.GRB.MINIMIZE)
    print "pong"
  # Write model to a file
    model.update()
    model.write('dense.lp')
    #print Q
    print np.linalg.eigvalsh(Q)
    #print "blub"
  # Solve
    model.setParam("PSDTol", float("inf"))
    model.optimize()
    print "blob"
    solution = np.ndarray((len(expandedTags)))
    if model.status == gurobipy.GRB.OPTIMAL:
        for i in range(solution.shape[0]):
            solution[i] = vars[i].x
        return True, solution
    else:
        return False



class SVR(object):

    options = [
    {"optimization" : "rf"},
    {"optimization" : "svr", "kernel" : "rbf"},
    {"optimization" : "svr", "kernel" : "linear"},
    {"optimization" : "svr", "kernel" : "poly"},
    {"optimization" : "svr", "kernel" : "sigmoid"},
    {"optimization" : "quadratic", "kernel" : "linear"},
    {"optimization" : "quadratic", "kernel" : "rbf"}
    #{"optimization" : "smo", "kernel" : "linear"},
    #{"optimization" : "smo", "kernel" : "gaussian"}
    ]


    def __init__(self, underMult, overMult, limitDensity = False, kernel =
                 "linear", optimization = "quadratic" ):
        """Parameters
        ----------
        X : {array-like, sparse matrix}, shape = [n_samples, n_features]
            Training vectors, where n_samples is the number of samples
            and n_features is the number of features.

        y : array-like, shape = [n_samples]
            Target values (class labels in classification, real numbers in
            regression)
        underMult : penalty-multiplier for underestimating density
        overMult : penalty-multiplier for overestimating the density
        """
        self.DENSITYBOUND=limitDensity
        self.upperBounds = [None, underMult, overMult]

        self.trained = False
        self.kernel = kernel
        self.optimization = optimization
        
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
   
    def fit(self, img, dot, sigma, smooth = True, normalize = False, epsilon =
            0.01):

        newImg, newDot, mapping, tags = \
        self.prepareData(img, dot, sigma, smooth, normalize)
        self.fitPrepared(newImg[mapping,:], newDot[mapping], tags, epsilon)

    def fitPrepared(self, img, dot, tags, epsilon, boxConstraints = []):
        

        numFeatures = img.shape[-1]
        numVariables = sum(img.shape[:-1])
        expandedTags = np.concatenate((np.ones(tags[0]), -1 * np.ones(np.sum(tags[1:])))).astype(np.int)
        if numVariables == 0:
            return False
        success = False
        tags.append(len(boxConstraints))

        if self.optimization == "rf":
            from sklearn.ensemble import RandomForestRegressor as RFR
            svr = RFR(n_jobs = 1)
            svr.fit(img, dot)

            #C = np.array([self.upperBounds[tag] for tag in tags], dtype = np.float)
            #svr.fit(img, dot, tags, sample_weight = C) 
            #svr.fit(img, dot) 
            #print svr.predict(img)
            #print svr.dual_coef_
            self.svr = svr
            success = True

        if self.optimization == "quadratic":
            B = img.view(np.matrix).reshape((numVariables, numFeatures))
            
            #Q = B * B.transpose()

            #debug_trace()
            #if self.kernel == "rbf":
            #    from sklearn.kernel_approximation import RBFSampler
            #    rbf_feature = RBFSampler(random_state = 1)
            #    B = rbf_feature.fit_transform(B)
            #Q = kernelize(B, tags, kernel = self.kernel, boxConstraints)
            #Q,c = kernelize(B, dot, tags, epsilon, self.kernel, boxConstraints)
            if self.kernel == "linear":
                #c = dot * (-expandedTags) + epsilon
                #success, alpha = optimizepossdef(tags, B, c, self.upperBounds, boxConstraints)

                Q,c = createKernel(B, dot, tags, epsilon, self.kernel, boxConstraints)
            #version 1 
                success, alpha = optimize(tags, Q, c, self.upperBounds)
            else:
                Q,c = createKernel(B, dot, tags, epsilon, self.kernel, boxConstraints)
            #version 1 
                success, alpha = optimize(tags, Q, c, self.upperBounds)
            #version 2
            #success, solution = optimizepossdef(tags, B, c, self.upperBounds, boxConstraints)
            
            
            alpha[np.where(alpha < 1E-5)] = 0
            #debug_trace()

            indices = np.nonzero(alpha)
            self.factors = alpha[indices] * expandedTags[indices]
            self.supportVectors = B[indices[0],:]

            #import sitecustomize
            #sitecustomize.debug_trace()
            if self.kernel == "linear":
                self.w = self.factors * self.supportVectors 
                residual = dot - np.matrix(img) * self.w.transpose()
            else:
                residual = dot - expandedTags * (np.matrix(alpha) * np.matrix(Q[:,:len(expandedTags)])).view(np.ndarray)
                residual = residual.flatten()
            self.b = self.findB(alpha[:sum(tags[:-1])], residual, expandedTags[:sum(tags[:-1])], self.upperBounds, epsilon)
                
            #self.w, self.b = self.convertAlphaToSol(alpha, tags,
            #                                   self.upperBounds, dot,
            #                                   epsilon)
        #elif self.optimization == "smo":
        #    smo = SMO(tags, img, dot, self.upperBounds, mapping)
        #    self.w, self.b,success = smo.mainLoop()
        elif self.optimization == "svr":
            from sklearn.svm import SVR as skSVR
            svr = skSVR(C = 1, epsilon = epsilon, kernel = self.kernel, gamma = 0.1)
            #svr = skSVR(C = 1, kernel = self.kernel, gamma = 0.05)
            C = np.array([self.upperBounds[tag] for tag in expandedTags], dtype = np.float)
            bcValues = []
            bcFeatures = np.array([],dtype = np.float)
            bcIndices = []
            for value, features in boxConstraints:
                bcValues.append(value)
                bcFeatures = np.concatenate((bcFeatures, features))
                bcIndices.append(np.sum(bcIndices) + features.shape[0])
            bcValues = np.array(bcValues, dtype = np.float)
            bcIndices = np.array(bcIndices, dtype = np.int)
            #svr.fit(img, dot, tags, sample_weight = C, bcValues = bcValues, bcFeatures = bcFeatures, bcIndices =
            #        bcIndices) 
            svr.fit(img, dot, expandedTags.astype(np.int8), sample_weight = C)
            #svr.fit(img, dot) 
            #print svr.predict(img)
            #print svr.dual_coef_
            self.svr = svr
            success = True
        if success:
            self.trained = True
        return success
    
    def predict(self, oldImage, normalize = False):
        if not self.trained:
            return np.zeros(oldImage.shape[:-1])
            #raise Exception("No training yet")
        oldShape = oldImage.shape
        image = np.copy(oldImage.reshape((-1, oldImage.shape[-1])))
        if normalize:
            image = sklearn.preprocessing.normalize(image, axis=0)
        if self.optimization == "svr":
            res = self.svr.predict(image)
            #print res
        elif self.optimization == "rf":
            res = self.svr.predict(image)

        elif self.optimization == "quadratic":
            if self.kernel == "linear":
                w,b = self.w, self.b
                res = np.squeeze(image *
                             w.transpose() + b)
                

        #elif self.optimization == "smo":
        #    w,b = self.w, self.b

            elif self.kernel == "rbf":

                #import sitecustomize
                #sitecustomize.debug_trace()
                #from sklearn.kernel_approximation import RBFSampler
                #rbf_feature = RBFSampler(gamma = 1, random_state = 1)
                #image = rbf_feature.fit_transform(image)
                num_features = image.shape[1]
                metric = "euclidean"
                transform = lambda x: np.exp(-(x**2) / (num_features * 1000))

                tmp = pairwise.pairwise_distances(image, self.supportVectors, metric = metric, n_jobs = -1)
                tmp = transform(tmp)

                res = np.matrix(tmp) * np.matrix(self.factors).transpose() + self.b

            elif self.kernel == "gaussian":
                gamma = 10000
                #debug_trace()
                res = spatial.distance.cdist(image, self.supportVectors, metric = "sqeuclidean") 
                res = -gamma * res
                res = np.matrix(np.exp(res)) * self.factors[:,None]
                res = res + b


        #res = np.zeros(oldShape[:-1])
        res = res.view(np.ndarray)
        res[np.where(res < 0)] = 0
        res.reshape(oldShape[:-1])
        return res

    def findB(self, alpha, residual, tags, limits, epsilon):

        pIndices = np.where(tags == 1)
        lIndices = np.where(tags == -1)

        lowPBound = np.where(alpha[pIndices] < limits[1])[0]
        lowP = residual[pIndices][lowPBound] - epsilon

        lowLBound = np.where(alpha[lIndices] > 0)[0]
        lowL = residual[lIndices][lowLBound] + epsilon

        highPBound = np.where(alpha[pIndices] > 0)[0]
        highP = residual[pIndices][highPBound] - epsilon
        
        highLBound = np.where(alpha[lIndices] < limits[-1])[0]
        highL = residual[lIndices][highLBound] + epsilon

        low = np.concatenate((lowL, lowP))
        high = np.concatenate((highL, highP))
        #print np.max(lowL), np.max(lowP), np.min(highL), np.min(highP)
        b = (np.min(high) + np.max(low)) / 2
        
        return b

    def convertAlphaToSol(self, alpha, x, tags, limits, y, epsilon):
        x_rel = x
        y_rel = y

        w = np.matrix(tags * alpha) * x_rel

        pIndices = np.where(tags == 1)
        lIndices = np.where(tags == -1)
        #debug_trace()
        #lowerBound = np.concatenate((np.where(alpha[pIndices] < limits[1])[0],
        #np.where(alpha[lIndices] > 0)[0]))
        #upperBound = np.concatenate((
        #np.where(alpha[pIndices] > 0)[0],
        #np.where(alpha[lIndices] < limits[-1])[0]))
        #low = -epsilon*tags[lowerBound] + y_rel[lowerBound] - (x_rel[lowerBound] *
        #w.transpose()).view(np.ndarray).flatten()
        residual = y_rel - (x_rel * w.transpose()).view(np.ndarray).flatten()


        lowPBound = np.where(alpha[pIndices] < limits[1])[0]
        lowP = residual[pIndices][lowPBound] - epsilon

        lowLBound = np.where(alpha[lIndices] > 0)[0]
        lowL = residual[lIndices][lowLBound] + epsilon

        highPBound = np.where(alpha[pIndices] > 0)[0]
        highP = residual[pIndices][highPBound] - epsilon
        
        highLBound = np.where(alpha[lIndices] < limits[-1])[0]
        highL = residual[lIndices][highLBound] + epsilon

        low = np.concatenate((lowL, lowP))
        high = np.concatenate((highL, highP))
        print np.max(lowL), np.max(lowP), np.min(highL), np.min(highP)
        b = 0 #TODO
        b = (np.min(high) + np.max(low)) / 2
        
        return w, b


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


