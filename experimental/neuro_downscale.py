import vigra, numpy, h5py 


#if options.destShape is not None:
            #result = numpy.zeros(options.destShape + (nch,), 'float32')
            #for i in range(nch):
                #cresult = vigra.filters.gaussianSmoothing(image[:,:,:,i].view(vigra.Volume), 2.0)
                #cresult = vigra.sampling.resizeVolumeSplineInterpolation(cresult,options.destShape)
                #result[:,:,:,i] = cresult[:,:,:]
            #image = result

fileraw = "/home/akreshuk/data/context/TEM_raw/50slices.h5"
filerawout = "/home/akreshuk/data/context/TEM_raw/50slices_down5.h5"

filelabels = "/home/akreshuk/data/context/TEM_labels/50slices.h5"
filelabelsout = "/home/akreshuk/data/context/TEM_labels/50slices_down5.h5"

coef = 0.2 #DANGER: downsample by 5, just for testing of classification
fr = h5py.File(fileraw)
fl = h5py.File(filelabels)

data = numpy.array(fr["data"])
labels = numpy.array(fl["data"])

shape = data.shape
newshape = [int(coef*x) for x in shape]
newshape[2] = 50
newshape = tuple(newshape)

tempdata = data.reshape(data.shape + (1,))
print tempdata.shape
#result = numpy.zeros(newshape)
result = vigra.filters.gaussianSmoothing(tempdata.astype(numpy.float32), (2.0, 2.0, 0.5))
result = vigra.sampling.resizeVolumeSplineInterpolation(result, newshape)
print result.shape

#data5d = numpy.zeros((1, result.shape[0], result.shape[1], result.shape[2], 1))
#data5d[0, :, :, :, 0]=result.squeeze()[:]

frout = h5py.File(filerawout, "w")
frout.create_dataset("/volume/data", data=result.squeeze())
frout.close()

labelsout = numpy.zeros(newshape+(1,))
templabels = numpy.zeros(labels.shape, dtype = numpy.float32)
for i in range(5):
    templabels[:]=0
    ind1 = numpy.where(labels==i+1)
    templabels[ind1] = 1
    result = vigra.filters.gaussianSmoothing(templabels.reshape(templabels.shape+(1,)), (2.0, 2.0, 0.5))
    result = vigra.sampling.resizeVolumeSplineInterpolation(result, newshape)
    indr = numpy.where(result>=0.5)
    labelsout[indr]=i+1
print labelsout.shape
flout = h5py.File(filelabelsout, "w")
flout.create_dataset("/volume/data", data=labelsout.squeeze())
flout.close()

#make an ilastik project for easier visualization

#frout5d = h5py.File("/home/akreshuk/data/context/TEM_raw/temp5d.h5")
#frout5d.create_dataset("/volume/data", data=data5d)
#frout5d.close()
