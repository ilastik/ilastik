from ilastik.array5d import Array5D, Roi5D, Point5D, Shape5D


import vigra
import numpy
a = vigra.taggedView(numpy.arange(10).reshape(2,5))
b = Array5D.view5D(a)

print(b.axistags)


a = Array5D.open_image("/home/tomaz/ilastikTests/SampleData/c_cells/cropped/cropped1.png")

roi = Shape5D(x=100, y=200).to_roi()
img = a.cut(roi).as_image()
