import numpy as np
from fastfilters import *


def differenceOfGaussian(array, sigma0, sigma1, window_size):
    return gaussianSmoothing(array, sigma0, window_size) - gaussianSmoothing(array, sigma1, window_size)


def maxStructureTensor(array, innerScale, outerScale, window_size):
    return np.amax(structureTensorEigenvalues(array, innerScale, outerScale, window_size), axis=3)


def maxHessianOfGaussian(array, scale, window_size):
    return np.amax(hessianOfGaussianEigenvalues(array, scale, window_size), axis=3)


FASTFILTERS = [
    {
        "function": gaussianSmoothing,
        "name": "gaussianSmoothing",
        "params": [
            # {
            #     "sigma": 0.3
            # },
            # {
            #     "sigma": 0.7
            # },
            {"sigma": 1.0},
            # {
            #     "sigma": 1.6
            # },
            # {
            #     "sigma": 3.5
            # },
            # {
            #     "sigma": 5.0
            # },
            # {
            #     "sigma": 10.0
            # }
        ],
    },
    {
        "function": laplacianOfGaussian,
        "name": "laplacianOfGaussian",
        "params": [
            # {
            #     "scale": 0.7
            # },
            {"scale": 1.0},
            # {
            #     "scale": 1.6
            # },
            # {
            #     "scale": 3.5
            # },
            # {
            #     "scale": 5.0
            # },
            # # {
            #     "scale": 10.0
            # }
        ],
    },
    #     {
    #         "function": gaussianGradientMagnitude,
    #         "name": "gaussianGradientMagnitude",
    #         "params": [
    #             # {
    #             #     "sigma": 0.7
    #             # },
    #             {
    #                 "sigma": 1.0
    #             },
    #             # {
    #             #     "sigma": 1.6
    #             # },
    #             {
    #                 "sigma": 3.5
    #             },
    #             {
    #                 "sigma": 5.0
    #             },
    #             # {
    #             #     "sigma": 10.0
    #             # }
    #         ]
    #     },
    #     {
    #         "function": maxStructureTensor,
    #         "name": "structureTensorEigenvalues",
    #         "params": [
    #             {
    #                 "innerScale": 0.7,
    #                 "outerScale": 1.4
    #             },
    #             # {
    #             #     "innerScale": 1.0,
    #             #     "outerScale": 2.0
    #             # },
    #             {
    #                 "innerScale": 1.6,
    #                 "outerScale": 3.2
    #             },
    #             # {
    #             #     "innerScale": 3.5,
    #             #     "outerScale": 7.0
    #             # },
    #             # {
    #             #     "innerScale": 5.0,
    #             #     "outerScale": 10.0
    #             # },
    #             # {
    #             #     "innerScale": 10.0,
    #             #     "outerScale": 20.0
    #             # }
    #         ]
    #     },
    #         {
    #         "function": maxHessianOfGaussian,
    #             "name": "hessianOfGaussianEigenvalues",
    #         "params": [
    #             # {
    #             #     "scale": 0.7
    #             # },
    #             {
    #                 "scale": 1.0
    #             },
    #             # {
    #             #     "scale": 1.6
    #             # },
    #             {
    #                 "scale": 3.5
    #             },
    #             # {
    #             #     "scale": 5.0
    #             # },
    #             # {
    #             #     "scale": 10.0
    #             # }
    #         ]
    #     },
    #     {
    #         "function": differenceOfGaussian,
    #         "name": "differenceOfGaussian",
    #         "params": [
    #             {
    #                 "sigma0": 0.7,
    #                 "sigma1": 0.7*0.66
    #             },
    #             # {
    #             #     "sigma0": 1.0,
    #             #     "sigma1": 1.0*0.66
    #             # },
    #             {
    #                 "sigma0": 1.6,
    #                 "sigma1": 1.6*0.66
    #             },
    #             # {
    #             #     "sigma0": 3.5,
    #             #     "sigma1": 3.5*0.66
    #             # },
    #             {
    #                 "sigma0": 5.0,
    #                 "sigma1": 5.0*0.66
    #             },
    # #             {
    # #                 "sigma0": 10.0,
    # #                 "sigma1": 10.0*0.66
    # #             }
    #         ]
    #     }
]
