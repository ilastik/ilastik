import requests
from ilastik.utility import flatten, unflatten, listify

def post(*args, **kwargs):
    resp = requests.post(*args, **kwargs)
    if resp.status_code != 200:
        raise Exception(resp.text)
    return resp


resp = post('http://localhost:5000/data_sources',
            data={'url': "/home/tomaz/ilastikTests/SampleData/c_cells/cropped/cropped1.png"})
data_source_id = resp.json()
print(f"data_source_id: {data_source_id}")


scribblings_path = '/home/tomaz/ilastikTests/SampleData/c_cells/cropped/cropped1_10_annotations_offset_by_188_124.png'
scribblings_raw = open(scribblings_path, 'rb').read()
resp = post('http://localhost:5000/annotations',
            files={'scribblings.arr': scribblings_raw},
            data={'scribblings.location.x': 188,
                  'scribblings.location.y': 124,
                  'raw_data': data_source_id})
annot_id = resp.json()
print(f"annot_id: {annot_id}")


resp = post('http://localhost:5000/feature_extractors/gaussian_smoothing',
            data={'sigma': 0.3})
gauss_id = resp.json()
print(f"gauss_id: {gauss_id}")


resp = post('http://localhost:5000/feature_extractors/hessian_of_gaussian',
            data={'sigma': 0.3})
hess_id = resp.json()
print(f"hess_id: {hess_id}")


resp = post('http://localhost:5000/pixel_classifier',
            data={
                'feature_extractor': gauss_id,
                'annotations.0': annot_id
            })
classifier_id = resp.json()
print(f"classifier_id: {classifier_id}")


resp = requests.get('http://localhost:5000/pixel_predictions', params={'pixel_classifier_id': classifier_id,
                                                                     'data_source_id': data_source_id,
                                                                     'x': '100_200',
                                                                     'y': '100_200'})
print(resp.status_code)
