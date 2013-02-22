
.. _axis-iterator:

==========================
Axis Iterator
==========================

Overview
============

The Axisiterator has been designed to provide a way to iterate through two volumes which is easy on the eye. An example of a typical use ist:


.. code-block:: python

 	it = AxisIterator(roi,srcGrid,trgtGrid)
	for src,trgt,mask in it:
		target[trgt] = operation_on_source(source[src])[mask]

trgt, src and mask represent slicings which can be applied to anything that implements the __getitem__(key) method, usually an n-dimensional array.
trgt specifies the slice in the target array, source specifies the slice in the source array. If the operation should inflate the data from the source
slice, the mask cuts it down to the appropriate size. The mask and trgt slices are always congruent.

.. _inner-mechanics:
Inner Mechanics
============

Consider the following example:

.. code-block:: python

	roi = Roi((10,10),(90,50))
	srcGrid = (20,40)
	trgtGrid = (40,20)
	it = AxisIterator(roi,srcGrid,trgtGrid)

It could be visualized like this:

.. figure:: images/iterator_exposition.svg
   :scale: 100  %
   :alt: iterator exposition
   

Using this:

.. code-block:: python

	for src,trgt,mask in it:
		print 'src ',src
		print 'trgt ',trgt
		print 'mask ',mask
		print '--------------------------------------------------'

One will get the following output:

.. code-block:: python

	src  (slice(0, 20, None), slice(0, 40, None))
	trgt  (slice(0, 30, None), slice(0, 10, None))
	mask  (slice(0, 30, None), slice(0, 10, None))
	--------------------------------------------------
	src  (slice(20, 40, None), slice(40, 80, None))
	trgt  (slice(30, 70, None), slice(10, 30, None))
	mask  (slice(0, 40, None), slice(0, 20, None))
	--------------------------------------------------
	src  (slice(40, 60, None), slice(80, 120, None))
	trgt  (slice(70, 80, None), slice(30, 40, None))
	mask  (slice(0, 10, None), slice(0, 10, None))
	--------------------------------------------------
	src  (slice(20, 40, None), slice(80, 120, None))
	trgt  (slice(30, 70, None), slice(30, 40, None))
	mask  (slice(0, 40, None), slice(0, 10, None))
	--------------------------------------------------
	src  (slice(40, 60, None), slice(40, 80, None))
	trgt  (slice(70, 80, None), slice(10, 30, None))
	mask  (slice(0, 10, None), slice(0, 20, None))
	--------------------------------------------------
	src  (slice(0, 20, None), slice(40, 80, None))
	trgt  (slice(0, 30, None), slice(10, 30, None))
	mask  (slice(0, 30, None), slice(0, 20, None))
	--------------------------------------------------
	src  (slice(0, 20, None), slice(80, 120, None))
	trgt  (slice(0, 30, None), slice(30, 40, None))
	mask  (slice(0, 30, None), slice(0, 10, None))
	--------------------------------------------------
	src  (slice(20, 40, None), slice(0, 40, None))
	trgt  (slice(30, 70, None), slice(0, 10, None))
	mask  (slice(0, 40, None), slice(0, 10, None))
	--------------------------------------------------
	src  (slice(40, 60, None), slice(0, 40, None))
	trgt  (slice(70, 80, None), slice(0, 10, None))
	mask  (slice(0, 10, None), slice(0, 10, None))
	--------------------------------------------------
	
As you can see, for every trgt slice there is a correspondig src and mask slice. In the first step the roi gets broken down in a number of trgt slices:


.. figure:: images/iterator_roiToTrgtSlices.svg
   :scale: 100  %
   :alt: roi being broken down into trgt slices
   
This is achieved by getSubRois(self,point,grid,roi),which calls nextStop(self,start,grid,roi) and nextStarts(self,point,grid,roi) repeatedly. For each point nextStarts() returns
the next points where either the grid intersects the grid itself or the roi. nextStop() returns for each starting point the stopping point, meaning the next point where the grid 
intersects itself or the roi AND the point where the volume of [start,stop] is greater then zero. Visualized:


.. figure:: images/iterator_nextStarts.svg
   :scale: 100  %
   :alt: getting all start points

When you have all starting points, nextStop() can be used to find the next stopping point, IF there is one. Two examples:

.. figure:: images/iterator_nextStop.svg
   :scale: 100  %
   :alt: assigning stopping points
   
The last step is of course merely conceptual. Once the trgt space is segmented into trgt slices, each trgt slice is mapped to a src slice. This is done using the mapRoiToSource() method. HOW this mapping is 
done is up to the developer. In the current implementation it fits the needs of image filtering. An illustration:

.. figure:: images/iterator_mapToSrc.svg
   :scale: 100  %
   :alt: mapping a trgt roi to the src roi

Now all that has to be done is to create the mask slice. Why is there a need for this? Sometimes the filter operation inflates the image and returns e.g. 3 channels even if you requested just one. The mask 
slice cuts out the desired part. Here is an illustration:

.. figure:: images/iterator_mask.svg
   :scale: 100  %
   :alt: mapping a trgt roi to the src roi
   
Finally src,trgt and mask slices are grouped together and returned.