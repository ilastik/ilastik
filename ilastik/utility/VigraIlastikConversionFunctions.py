# a selection of often used function for easy usage
# to use ilastik slots and vigra functions

import numpy as np

def removeLastAxis(array):
    """
    Remove the last dimension of array 

    :param array: where last axis should be removed
    :return: array with removed last axis
    """
    #cut off the channel dimension
    array          = array.reshape(array.shape[0:-1])
    return array
def removeFirstAxis(array):
    array          = array.reshape(array.shape[1:])
    return array

def addFirstAxis(array):
    arrayOut = array[np.newaxis,...]
    return arrayOut

def addLastAxis(array):
    """
    add a new dimension as last dimension to the array
    this intends to restore the channel dimension, or other dimensions

    :param array: array for operation
    :return: the new array with an addtional axis at the end
    """
    # add axis at last place
    arrayOut = array[...,np.newaxis]
    return arrayOut



def getArray(slot):
    """
    get the arrays from given slot
    :return: array
    """
    #get the data from boundaries and seeds
    array    = slot[:].wait()
    return array



def evaluateSlicing(slot):
    """
    check whether the channel is the last axis
    check whether the time axis is used or not

    :param slot: use the data of the given slot
    :return: tUsed True if time-axis is used, else: False
        tId: the index of the time Axis
    """
    # get dimesions
    tags = slot.meta.axistags
    xId = tags.index('x')
    yId = tags.index('y')
    zId = tags.index('z')
    tId = tags.index('t')
    cId = tags.index('c')
    #number of dimensions
    dims = len(slot.meta.shape)

    # channel dimension must be the last one
    assert cId == dims - 1

    #controlling for 2D, 2D with time, 3D, 3D with slicing 
    tUsed = True if (tId < dims) else False
    # error if x, y, or c can't aren't used
    if (cId >= dims or xId >= dims or yId >= dims):
        logger.info("no channel, x or y used in data; something is probably wrong")

    return (tUsed, tId)
