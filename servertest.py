import requests
import json
import numpy
from ilastik.utility import flatten, unflatten, listify
from ndstructs import Array5D

def post(*args, **kwargs):
    return send('post', *args, **kwargs)

def get(*args, **kwargs):
    return send('get', *args, **kwargs)

def send(method:str, *args, **kwargs):
    resp = getattr(requests, method)(*args, **kwargs)
    if resp.status_code != 200:
        raise Exception(resp.text)
    return resp


resp = post('http://localhost:5000/data_source',
            data={'url': "/home/tomaz/SampleData/n5tests/317_8_CamKII_tTA_lacZ_Xgal_s123_1.4.n5/data"})


resp = post('http://localhost:5000/data_source',
            data={'url': "/home/tomaz/ilastikTests/SampleData/c_cells/cropped/cropped1.png"})
data_source_id = resp.json()
print(f"data_source_id: {data_source_id}")
assert data_source_id.startswith("pointer@")


scribblings_path = '/home/tomaz/ilastikTests/SampleData/c_cells/cropped/cropped1_10_annotations_offset_by_188_124.png'
scribblings_raw = open(scribblings_path, 'rb').read()
resp = post('http://localhost:5000/annotation',
            files={'scribblings.arr': scribblings_raw},
            data={'scribblings.location.x': 188,
                  'scribblings.location.y': 124,
                  'raw_data': data_source_id})
annot_id = resp.json()
print(f"annot_id: {annot_id}")
assert annot_id.startswith("pointer@")


resp = post('http://localhost:5000/gaussian_smoothing',
            data={'sigma': 0.3})
gauss_id = resp.json()
print(f"gauss_id: {gauss_id}")
assert gauss_id.startswith("pointer@")


resp = post('http://localhost:5000/hessian_of_gaussian_eigenvalues',
            data={'scale': 0.3})
hess_id = resp.json()
print(f"hess_id: {hess_id}")
assert hess_id.startswith("pointer@")

resp = get('http://localhost:5000/feature_extractor')
print("Feature extractors:")
print(json.dumps(resp.json(), indent=4))

resp = get(f'http://localhost:5000/feature_extractor/{hess_id}').json()
print("Retrieveing hessian filter:\n", json.dumps(resp, indent=4))


resp = post('http://localhost:5000/pixel_classifier',
            data={
                'feature_extractors.0': gauss_id,
                'feature_extractors.1': hess_id,
                'annotations.0': annot_id
            })
classifier_id = resp.json()
print(f"classifier_id: {classifier_id}")
assert classifier_id.startswith("pointer@")


resp = get('http://localhost:5000/predict', params={'pixel_classifier_id': classifier_id,
                                                    'data_source_id': data_source_id,
                                                    'x': '100_200',
                                                    'y': '100_200'})


info = get(f"http://localhost:5000/predictions/{classifier_id}/{data_source_id}/info").json()
print(json.dumps(info, indent=4))

resp = post('http://localhost:5000/ng_annotation',
            data={
                'voxels.0.x': 137,
                'voxels.0.y': 112,
                'voxels.0.z':  0,

                'voxels.1.x': 157,
                'voxels.1.y': 102,
                'voxels.1.z': 0,

                'color.0': 212,
                'color.1': 212,
                'color.2': 212,

                'raw_data': data_source_id
            })


predictions_path = f"predictions/{classifier_id}/{data_source_id}"
binary = get(f"http://localhost:5000/{predictions_path}/data/0-256_0-256_0-1").content
data = numpy.frombuffer(binary, dtype=numpy.uint8).reshape(2, 256, 256)
a = Array5D(data, axiskeys='cyx')
a.show_channels()

print("Use this URL in neuroglancer::::")
print("\nPredictions:")
print(f"precomputed://http://localhost:5000/{predictions_path}")

print("\nRaw:")
print(f"precomputed://http://localhost:5000/datasource/{data_source_id}")


print("\n\nRgb squares url:")
resp = post('http://localhost:5000/data_source',
            data={'url': "/home/tomaz/ilastikTests/SampleData/rgbtest/rgb_squares_rgb_no-alpha.png"})
rgb_squares_data_source_id = resp.json()
print(f"precomputed://http://localhost:5000/datasource/{rgb_squares_data_source_id}")
binary = get(f"http://localhost:5000/datasource/{rgb_squares_data_source_id}/data/0-10_0-10_0-1").content
data = numpy.frombuffer(binary, dtype=numpy.uint8).reshape(3, 10, 10)
a = Array5D(data, axiskeys='cyx')
a.show_channels()


import pydevd; pydevd.settrace()
resp = post('http://localhost:5000/data_source',
            data={'url': "/home/tomaz/SampleData/n5tests/bunch_of_cells_Probabilities.n5/exported_data"})
data_source_id = resp.json()
predictions_path = f"predictions/{classifier_id}/{data_source_id}"
binary = get(f"http://localhost:5000/{predictions_path}/data/0-256_0-256_0-1").content
data = numpy.frombuffer(binary, dtype=numpy.uint8).reshape(2, 256, 256)
a = Array5D(data, axiskeys='cyx')
a.show_channels()


