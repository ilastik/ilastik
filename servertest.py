import requests
from ilastik.utility import flatten, unflatten, listify

def post(*args, **kwargs):
    resp = requests.post(*args, **kwargs)
    if resp.status_code != 200:
        raise Exception(resp.text)
    return resp


resp = post('http://localhost:5000/data_sources',
            data={'url': "/home/tomaz/ilastikTests/SampleData/c_cells/cropped/cropped1.png"})
ds_id = resp.json()
print(f"ds_id: {ds_id}")

scribblings_path = '/home/tomaz/ilastikTests/SampleData/c_cells/cropped/cropped1_10_annotations_offset_by_188_124.png'
scribblings_raw = open(scribblings_path, 'rb').read()
resp = post('http://localhost:5000/annotations',
            files={'scribblings.arr': scribblings_raw},
            data={'scribblings.location.x': 188,
                  'scribblings.location.y': 124,
                  'raw_data': ds_id})
print(resp.text)


