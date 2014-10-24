
.. _lazyflow-classifiers:

===========
Classifiers
===========

.. currentmodule:: lazyflow.classifiers

Lazyflow includes some predefined operators for training a classifier and predicting results with it.  
These operators are defined in ``lazyflow.operators.classifierOperators.py``.  
Most applications should use the high-level operators ``OpTrainClassifierBlocked`` and ``OpClassifierPredict``, 
which instantiate internal pipelines for retrieving blocks of image data, caching it, and using it with the classifier.

The lazyflow classifiers operators support two families of classifiers:

1. Most classifiers are so-called "vectorwise" classifiers, which can be trained with a simple feature matrix.  
When training these classifiers, the features for each label can be extracted from the input images and cached in a small feature matrix.

2. But some classifiers require the training data in its full 2D or 3D context, in which case it is trained with full 2D/3D feature images.  
In lazyflow, these are called "pixelwise" classifiers.

The classifier operators are made to be agnostic with respect to the particular type of classifier you want to use (e.g. RandomForest, SVM, etc.)
Any type of classifier can be used as long as it is made to adhere to two special abstract interfaces: a 
'classifier factory' interface and a 'classifier' interface.

To add support for a new classifier in lazyflow, you must define two classes:

1. A "classifier factory", which inherits from either ``LazyflowVectorwiseClassifierFactoryABC`` or ``LazyflowPixelwiseClassifierFactoryABC``
2. A "classifier" which inherits from either ``LazyflowVectorwiseClassifierABC`` or `LazyflowPixelwiseClassifierABC``

The factory is used to create and train a classifier.  The factory must be pickle-able and the classifier must be serializable in hdf5.

For clear example implementations of vectorwise and pixelwise classifiers, see `vigraRfLazyflowClassifier.py`_ and `vigraRfPixelwiseClassifier.py`_.
A slightly more complicated "production" classifier can be found in `parallelVigraRfLazyflowClassifier.py`_.

.. _vigraRfLazyflowClassifier.py: https://github.com/ilastik/lazyflow/blob/master/lazyflow/classifiers/vigraRfLazyflowClassifier.py
.. _vigraRfPixelwiseClassifier.py: https://github.com/ilastik/lazyflow/blob/master/lazyflow/classifiers/vigraRfPixelwiseClassifier.py
.. _parallelVigraRfLazyflowClassifier.py: https://github.com/ilastik/lazyflow/blob/master/lazyflow/classifiers/parallelVigraRfLazyflowClassifier.py

Finally, most classifiers used in ``sklearn`` can be used in lazyflow via the classes implemented in `sklearnLazyflowClassifier.py`_.

.. _sklearnLazyflowClassifier.py: https://github.com/ilastik/lazyflow/blob/master/lazyflow/classifiers/sklearnLazyflowClassifier.py

.. note:: In the ilastik pixel classification workflow, the classifier type can be changed via the "Advanced" menu, 
          which is only visible in "debug" mode.


Reference: Classifier ABCs
==========================

.. autoclass:: LazyflowVectorwiseClassifierFactoryABC
   :members:

.. autoclass:: LazyflowVectorwiseClassifierABC
   :members:

.. autoclass:: LazyflowPixelwiseClassifierFactoryABC
   :members:

.. autoclass:: LazyflowPixelwiseClassifierABC
   :members:
