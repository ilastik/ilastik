import matplotlib.pyplot as plt
import matplotlib
import numpy as np
from scipy import ndimage
import sklearn
from sklearn import preprocessing
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


def kernelize(B, tags, kernel):
    coeff = tags[:,None] * tags[None,:]
    if kernel == "linear":
        Q = np.multiply(coeff,(B * B.transpose()))
        #debug_trace()
        return Q
    elif kernel == "gaussian":
        gamma = 10000
        #debug_trace()
        Q = spatial.distance.pdist(B, metric="sqeuclidean")
        Q = -gamma * Q
        Q = np.exp(spatial.distance.squareform(Q))
        Q = np.multiply(coeff,Q)
        return Q

def optimizepossdef(tags, B, c, upperBounds):
    pass
    B = np.multiply(tags[:,None], B) 
    model = gurobipy.Model()

    for j in range(tags.shape[0]):
        model.addVar(lb=0., ub=float(upperBounds[tags[j]]), vtype=gurobipy.GRB.CONTINUOUS)

    model.update()
    vars = model.getVars()

    expr = gurobipy.LinExpr()
    for j in range(tags.shape[0]):
        expr += -tags[j]*vars[j]

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
    solution = np.ndarray((tags.shape[0]))
    if model.status == gurobipy.GRB.OPTIMAL:
        for i in range(solution.shape[0]):
            solution[i] = vars[i].x
        return True, solution
    else:
        return False



class SMO:

    def __init__(self, tags, X,Y, upperBounds, mapping = None, epsilon = 0):
        if mapping == None:
            mapping = np.arange((X.shape[0]))
        
        self.X = X[mapping,:]
        self.Y = Y[mapping]
        self.w = np.zeros((X.shape[1]))
        self.bounds = [upperBounds[tag] for tag in tags]
        self.tags = tags

        self.numVariables = len(tags)
        self.numPos = len(np.where(tags == 1)[0])
        self.numL = self.numVariables - self.numPos
        #get all residuals
        self.alpha = np.zeros((self.numVariables))
        #select i and j
        #import random
        self.I = np.concatenate(
            (np.ones((self.numPos)) * 1,
            np.ones((self.numL)) * 4)
        )

        self.fcache = np.empty((self.numVariables)) * np.nan
        self.blow = -float('inf')
        self.ilow = 0
        self.bup = float('inf')
        self.iup = self.numPos
        self.tol = 1E-6 #machine tolerance
        self.eps = epsilon #epsilon in the SVR formulation
        
    def checkAlpha(self, tag, alpha, bound):
        if tag == 1:
            if alpha == 0:
                return 1
            elif alpha == bound:
                return 3
        else:
            if alpha == 0:
                return 4
            elif alpha == bound:
                return 2


    def eval(self, i):
        val = np.nan
        try:
            val = np.sum(self.X[i,:] * self.w)
        except:
            debug_trace()
        return val

    def examine(self, i2):
        #print "ping"
        y2 = self.Y[i2]
        alpha2 = self.alpha[i2]
        F2 = self.fcache[i2]
        if np.isnan(F2):
            #compute value for F2
            F2 = (y2 - self.tags[i2] * self.eps) - self.eval(i2)
            self.fcache[i2] = F2
        if self.I[i2] in [1,2] and F2 > self.blow:
            self.blow = F2
            self.ilow = i2
        elif self.I[i2] in [3,4] and F2 < self.bup:
            self.bup = F2
            self.iup = i2

        optimality = True
        i1 = -1
        if self.I[i2] in [0,3,4]:
            if self.blow - F2 > 2* self.eps:
                optimality = False
                i1 = self.ilow
        if self.I[i2] in [0,1,2]:
            if F2 - self.bup > 2* self.eps:
                optimality = False
                i1 = self.iup

        if optimality == True:
            return 0
        
        if self.I[i2] is 0:
            if self.blow - F2 > F2 - self.bup:
                i1 = self.ilow
            else:
                i1 = self.iup

        return self.takeStep(i1, i2)



    def mainLoop(self):
        #debug_trace()
        checkAllIndices = True
        numChanged = 0
        finished = False
        while True:
            #print "loopStart"
            numChanged = 0

            if checkAllIndices:
                for i in range(len(self.I)):
                    numChanged = numChanged + self.examine(i)
                    #print self.blow, self.bup
                    #print self.w
                    #print numChanged
                if numChanged == 0:
                    finished = True

            for i in range(len(self.I)):
                if self.I[i] == 0:
                    numChanged = numChanged + self.examine(i)

            #if self.bup > self.blow - 2* self.tol:
            #    numChanged = 0
            
            if finished == True:
                break
            elif numChanged == 0:
                checkAllIndices = True
        #debug_trace()
        self.b = 0.5 * (self.bup + self.blow)
        return np.matrix(self.w), self.b, 1

    def scp(self, x1, x2):
        return np.sum(x1 * x2)

    def takeStep(self, i1, i2):

        if i1 == i2: 
            return 0
        y1 = self.Y[i1]
        F1 = self.fcache[i1]
        if np.isnan(F1):
            F1 = (y1 - self.tags[i1] * self.eps) - self.eval(i1)
            #debug_trace()
        #y2 = self.Y[i2]
        F2 = self.fcache[2]
        if np.isnan(F2):
            print "beep"
            #debug_trace()
        #force F1 > F2, 
        #print "F1, F2: ", F1, F2
        if F1 < F2:
            i1,i2 = i2,i1
            F1,F2 = F2,F1
        #print "F1, F2: ", F1, F2
         
        alpha1 = self.alpha[i1]
        alpha2 = self.alpha[i2]
        x1 = self.X[i1,:]
        x2 = self.X[i2,:]
        x1x1 = self.scp(x1,x1)
        x2x2 = self.scp(x2,x2)
        x1x2 = self.scp(x1,x2)

#        def checkValue(a1, a2):
#            y2 = self.Y[i2]
#`            _quad = 0.5 * (a1 * x1x1 * a1 + 2 * a1 * a2 * x1x2 + a2 * x2x2 * a2)
#            _lin = self.tags[i1] * a1 * y1 + self.tags[i2] * a2 * y2 + self.eps * a1 + self.eps * a2
#            return _quad + _lin

#        def checkUpdate(a1, a2, delta):
#            #delta = -tags[2] * d
#            #a2_new = a2 + delta
#            #a1_new = a1 - tags[1] * tags[2] * delta
#            y2 = self.Y[i2]
#            _quad = 0.5 * (a1 * x1x1 * a1 + 2 * a1 * a2 * x1x2 + a2 * x2x2 * a2)
#            _quad_new = _quad + 0.5 * 
#            (
#             delta**2 * x2x2 + 2 * x2x2 * a2 * delta +
#             delta**2 * x1x1 - 2 * x1x1 * a1 * delta * tags[1] * tags[2]+
#             2 * x1x2 * (a1 * delta - a2 * tags[1] * tags[2] + delta**2 * tags[1] * tags[2]  )
#            )
#            _lin = self.tags[i1] * a1 * y1 + self.tags[i2] * a2 * y2 + self.eps * a1 + self.eps * a2
#            return _quad + _lin


        #print x1,x2
        #print x1x1,x1x2, x2x2
        #reverse engineer delta:  
        eta = x1x1 + x2x2 - 2 * x1x2
        print "eta: ", eta
        lamb = float('inf')
        print "before", checkValue(alpha1, alpha2)
        if eta > 0:
            lamb = (F1 - F2) / eta
        #b2 = [np.nan, self.bounds[i2] - self.alpha[i2], self.alpha[i2]]
        #b1 = [np.nan, self.alpha[i1], self.bounds[i1] - self.alpha[i1]]
        b1 = [np.nan, self.bounds[i1] - self.alpha[i1], self.alpha[i1]]
        b2 = [np.nan, self.alpha[i2], self.bounds[i2] - self.alpha[i2]]
        lambClipped = min(lamb, b1[self.tags[i1]], b2[self.tags[i2]])

        delta2 = -lambClipped * self.tags[i2]
        if abs(lambClipped) < self.tol * (self.alpha[i2] + lambClipped + self.tol):
            return 0
        #delta1 = self.tags[i1] * delta
        #delta2 = self.tags[i2] * delta
        s = self.tags[i1] * self.tags[i2]
        delta1 = -s * delta2
        #check boundaries:

       
        self.alpha[i1] = alpha1 + delta1
        self.alpha[i2] = alpha2 + delta2
        print "after", checkValue(self.alpha[i1], self.alpha[i2])

        for i in [i1, i2]:
            self.I[i] = 0
            if self.tags[i] == 1:
                if self.alpha[i] == 0:
                    self.I[i] = 1
                elif self.alpha[i] == self.bounds[i]:
                    self.I[i] = 3
            else:
                if self.alpha[i] == 0:
                    self.I[i] = 4
                elif self.alpha[i] == self.bounds[i]:
                    self.I[i] = 2
        

        self.updateW(i1, i2, delta1, delta2)
        #print "fcache ", self.fcache
        self.fcache[i1]= self.fcache[i1] - self.tags[i1] * delta1 * x1x1 - \
        self.tags[i2] * delta2 * x1x2
        self.fcache[i2]= self.fcache[i2] - self.tags[i2] * delta2 * x2x2 - \
        self.tags[i1] * delta1 * x1x2
        #print (y1 - self.tags[i1] * self.eps) - self.eval(i1)
        #print (self.Y[i2] - self.tags[i2] * self.eps) - self.eval(i2)
        #print "fcache ", self.fcache
        for i in [i1, i2]:
            F = self.fcache[i]
                
            if self.I[i] in [0,1,2]:
                self.blow = F
                self.ilow = i
            if self.I[i] in [0,3,4]:
                self.bup = F
                self.iup = i
        #print "beep", self.blow, self.bup
            
        self.sanityCheck()
        return 1

    def sanityCheck(self):
        pass
    def updateW(self, i1, i2, delta1, delta2):
        self.w = self.w + self.tags[i1] * delta1 * self.X[i1,:]
        self.w = self.w + self.tags[i2] * delta2 * self.X[i2,:]
        
        #self.w = np.squeeze(np.matrix(self.tags * self.alpha) * self.X)


def optimize(tags, Q, c, upperBounds):

    model = gurobipy.Model()

    # Add variables to model
    for j in range(tags.shape[0]):
        model.addVar(lb=0., ub=float(upperBounds[tags[j]]), vtype=gurobipy.GRB.CONTINUOUS)

    model.update()
    vars = model.getVars()

    expr = gurobipy.LinExpr()
    for j in range(tags.shape[0]):
        expr += tags[j]*vars[j]

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
    print "blub"
  # Solve
    model.optimize()
    print "blob"
    solution = np.ndarray((tags.shape[0]))
    if model.status == gurobipy.GRB.OPTIMAL:
        for i in range(solution.shape[0]):
            solution[i] = vars[i].x
        return True, solution
    else:
        return False

def convertAlphaToSol(alpha, x, tags, limits, y, epsilon):
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
    #print np.max(lowL), np.max(lowP), np.min(highL), np.min(highP)
    b = 0 #TODO
    b = (np.min(high) + np.max(low)) / 2
    
    return w, b



class SVR(object):

    options = [
    {"optimization" : "svr", "kernel" : "rbf"},
    {"optimization" : "svr", "kernel" : "linear"},
    {"optimization" : "svr", "kernel" : "poly"},
    {"optimization" : "svr", "kernel" : "sigmoid"},
    {"optimization" : "quadratic", "kernel" : "linear"},
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
        nindices = np.ravel_multi_index(backupindices, dot.shape)
        dot = dot.reshape(-1)
        img = np.copy(oldImg.reshape((-1,oldImg.shape[-1])))
        if normalize:
            img = sklearn.preprocessing.normalize(img, axis=0)
        pindices = np.where(dot > 0.01)[0]
        lindices = None
        if self.DENSITYBOUND:
            lindices = np.concatenate((nindices, pindices))
        else:
            lindices = nindices

        #lindices = np.concatenate((pindices, nindices))
        numVariables = len(pindices) + len(lindices) 

        mapping = np.concatenate((pindices, lindices))

        tags = np.zeros(numVariables,dtype=np.int8)
        tags[0:len(pindices)] = 1
        tags[len(pindices):] = -1
        #print dot
        self.dot = dot
        self.img = img

        return img, dot, mapping, tags
   
    def fit(self, img, dot, sigma, smooth = True, normalize = False, epsilon =
            0.01):

        newImg, newDot, mapping, tags = \
        self.prepareData(img, dot, sigma, smooth, normalize)
        self.fitPrepared(newImg[mapping,:], newDot[mapping], tags, epsilon)

    def fitPrepared(self,img, dot, tags, epsilon):
        
        numFeatures = img.shape[-1]
        numVariables = len(tags)
        if numVariables == 0:
            return False
        success = False
        if self.optimization == "quadratic":
            B = np.ndarray((numVariables, numFeatures))
            #B[0:len(pindices), :] = img[pindices,:]
            #B[len(pindices):, :] = img[lindices,:] 
            B[:,:] = img
            B = np.matrix(B)
            
            #Q = B * B.transpose()

            c = dot * (-tags)+ epsilon
            Q = kernelize(B, tags, kernel = self.kernel)
            #debug_trace()
            #version 1 
            #success, solution = optimize(tags, Q, c, self.upperBounds)
            #version 2
            success, solution = optimizepossdef(tags, B, c, self.upperBounds)
            
            
            solution[np.where(solution < 1E-5)] = 0
            #debug_trace()

            indices = np.where(solution)
            self.factors = solution[indices]
            self.supportVectors = B[indices[0],:]
            self.w, self.b = convertAlphaToSol(solution, img, tags,
                                               self.upperBounds, dot,
                                               epsilon)
        #elif self.optimization == "smo":
        #    smo = SMO(tags, img, dot, self.upperBounds, mapping)
        #    self.w, self.b,success = smo.mainLoop()
        elif self.optimization == "svr":
            from sklearn.svm import SVR as skSVR
            svr = skSVR(C = 1, epsilon = epsilon, kernel = self.kernel)
            C = np.array([self.upperBounds[tag] for tag in tags], dtype = np.float)
            svr.fit(img, dot, tags, sample_weight = C) 
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
        else:
            w,b = None,None
            if self.optimization == "quadratic":
                w,b = self.w, self.b
            elif self.optimization == "smo":
                w,b = self.w, self.b

            res = np.zeros(oldShape[:-1])
            if self.kernel == "linear":
                res = np.squeeze(image *
                             w.transpose() + b)
            elif self.kernel == "gaussian":
                gamma = 10000
                #debug_trace()
                res = spatial.distance.cdist(image, self.supportVectors, metric = "sqeuclidean") 
                res = -gamma * res
                res = np.matrix(np.exp(res)) * self.factors[:,None]
                res = res + b


        res[np.where(res < 0)] = 0
        res.reshape(oldShape[:-1])
        return res


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
    img = img[...,:]
    #img = img[..., None]
    
    DENSITYBOUND=True
    pMult = 100 #This is the penalty-multiplier for underestimating the density
    lMult = 100 #This is the penalty-multiplier for overestimating the density


   #ToyExample
#    img = np.ones((9,9,1),dtype=np.float32)
#    dot = np.zeros((9,9))
#    img = 1 * img
#    #img[:,:,1] = np.random.rand(*img.shape[:-1])
#    #img[0,0] = 3
#    #img[1,1] = 3
#    img[3:6,3:6] = 50
#    dot[4,4] = 2
#    dot[0,0] = 1
#    dot[1,1] = 1

    backup_image = np.copy(img)
    Counter = SVR(pMult, lMult, DENSITYBOUND, kernel = "rbf", optimization =
                 "svr")
    sigma = [4]
    testimg, testdot, testmapping, testtags = Counter.prepareData(img, dot,
                                                                  sigma,
                                                                  normalize =
                                                                  False, smooth
                                                                  = True
                                                                  )
    #print "blub", testimg.shape
    #print testimg
    #print testdot, np.sum(testdot)
    success = Counter.fit(img, dot, sigma, epsilon = 0.001, smooth = True, normalize
                          = False)
    #print Counter.w, Counter.


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
    newdot = Counter.predict(backup_image, normalize = False)

    print "prediction"
    #print img
    #print newdot
    print "sum", np.sum(newdot)
    
    fig = plt.figure()
    fig.add_subplot(1,3,1)
    plt.imshow(testimg[...,0].astype('uint8').reshape(backup_image.shape[:-1]), cmap=matplotlib.cm.gray)
    fig.add_subplot(1,3,2)
    plt.imshow(newdot.reshape(backup_image.shape[:-1]), cmap=matplotlib.cm.gray)
    fig.add_subplot(1,3,3)
    plt.imshow(testdot.reshape(backup_image.shape[:-1]), cmap=matplotlib.cm.gray)
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


    plt.show()
