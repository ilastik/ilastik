from lazyflow import operators
from lazyflow.graph import *

import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)


g = Graph()


datafile = "/home/akreshuk/data/context/TEM_raw/50slices_down2_42.h5"
h5path = "/volume/data"
import h5py
f = h5py.File(datafile)
image = numpy.array(f[h5path])
image = image.squeeze()
image = image.reshape(image.shape+(1,))
imageva = vigra.VigraArray(image, axistags=vigra.VigraArray.defaultAxistags(3))

#Same sigmas as in Classification Workflow"
#sigmas = [0.7, 1.0, 1.6, 3.5, 5]
sigma = 3.5

#Gaussian smoothing
opa = operators.OpGaussianSmoothing(g)
#opa.inputs["Input"].connect(slicer.outputs["Slices"])
opa.inputs["Input"].setValue(imageva)
opa.inputs["sigma"].setValue(sigma)
#stacker_opa = operators.OpMultiArrayStacker(g)
#stacker_opa.inputs["Images"].connect(opa.outputs["Output"])
#stacker_opa.inputs["AxisFlag"].setValue('z')
#stacker_opa.inputs["AxisIndex"].setValue(2)

gaus = opa.outputs["Output"][:].allocate().wait()
#gausfile = h5py.File("/home/akreshuk/data/context/TEM_results/gaus35.h5", "w")
#d = numpy.zeros((1,)+gaus.shape)
#d[:] = gaus
#gausfile.create_dataset("/volume/data", data=d)
#gausfile.close()

#no operator, compute directly

smoothed = vigra.filters.gaussianSmoothing(imageva, sigma)
print "compare direct"

for i in range(gaus.shape[0]):
    for j in range(gaus.shape[1]):
        if abs(gaus[i, j, 0]-smoothed[i, j, 0])>1:
            print i, j, gaus[i, j, 0], smoothed[i, j, 0]

print "compare with old"
oifile = h5py.File("/home/akreshuk/data/context/TEM_raw/gaus35oi.h5")
oidata = oifile["/volume/data"]
for i in range(gaus.shape[0]):
    for j in range(gaus.shape[1]):
        if abs(gaus[i, j, 0]-oidata[0, 0, i, j, 0])>1:
            print i, j, gaus[i, j, 0], oidata[0, 0, i, j, 0]
            
print "compare old and direct"
for i in range(gaus.shape[0]):
    for j in range(gaus.shape[1]):
        if abs(smoothed[i, j, 0]-oidata[0, 0, i, j, 0])>0.01:
            print i, j, gaus[i, j, 0], oidata[0, 0, i, j, 0]

#HOG
hog = operators.OpHessianOfGaussianEigenvalues(g)
hog.inputs["Input"].setValue(imageva)
hog.inputs["scale"].setValue(sigma)
hogout = hog.outputs["Output"][:].allocate().wait()
print "hog"
hogoutdir = vigra.filters.hessianOfGaussianEigenvalues(imageva, sigma)
for i in range(hogout.shape[0]):
    for j in range(hogout.shape[1]):
        if abs(hogout[i, j, 0]-hogoutdir[i, j,0])>1:
            print i, j, hogout[i, j, 0], hogoutdir[i, j, 0]
            
strten = operators.OpStructureTensorEigenvalues(g)
strten.inputs["Input"].setValue(imageva)
strten.inputs["innerScale"].setValue(sigma)
strten.inputs["outerScale"].setValue(0.5*sigma)
strtenout = strten.outputs["Output"][:].allocate().wait()
strtenoutdir = vigra.filters.structureTensorEigenvalues(imageva, sigma, sigma/2.0)
print "structure tensor"
for i in range(strtenout.shape[0]):
    for j in range(strtenout.shape[1]):
        if abs(strtenout[i, j, 0]-strtenoutdir[i, j,0])>5:
            print i, j, strtenout[i, j, 0], strtenoutdir[i, j, 0]

print "diff of gaussians:"
diff = operators.OpDifferenceOfGaussians(g)
diff.inputs["Input"].setValue(imageva)
diff.inputs["sigma0"].setValue(sigma)            
diff.inputs["sigma1"].setValue(sigma*0.66)
diffout = diff.outputs["Output"][:].allocate().wait()
diffoutdir = vigra.filters.gaussianSmoothing(imageva, sigma)-vigra.filters.gaussianSmoothing(imageva, sigma*0.66)
for i in range(diffout.shape[0]):
    for j in range(diffout.shape[1]):
        if abs(diffout[i, j, 0]-diffoutdir[i, j,0])>5:
            print i, j, diffout[i, j, 0], diffoutdir[i, j, 0]

print "laplacian"
lap = operators.OpLaplacianOfGaussian(g)
lap.inputs["Input"].setValue(imageva)
lap.inputs["scale"].setValue(sigma)
lapout = lap.outputs["Output"][:].allocate().wait()
lapoutdir = vigra.filters.laplacianOfGaussian(imageva, sigma)
for i in range(lapout.shape[0]):
    for j in range(lapout.shape[1]):
        if abs(lapout[i, j, 0]-lapoutdir[i, j,0])>5:
            print i, j, lapout[i, j, 0], lapoutdir[i, j, 0]

