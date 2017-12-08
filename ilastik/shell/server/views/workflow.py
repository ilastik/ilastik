from apistar import get_current_app, Response
from ..tools import log_function_call, time_function_call
from ..ilastikAPItypes import RoiType
import json
import io
import logging
import numpy as np
import z5py

logger = logging.getLogger(__name__)


@time_function_call(logger=logger)
def get_structured_info():
    dataset_names, json_states = get_current_app()._ilastik_api.get_structured_info()
    resp = {
        'states': json_states,
        'image_names': dataset_names,
        'message': 'Structured info retrieval successful'
    }
    return resp

@time_function_call(logger=logger)
def get_data(dataset_name: str, source_name: str, format: str, roi_begin: str, roi_end: str) -> Response:
    print(dataset_name, source_name, format, roi_begin, roi_end)
    start = map(int, roi_begin.split('_'))
    stop = map(int, roi_end.split('_'))
    slot = get_current_app()._ilastik_api.slot_tracker.get_slot(dataset_name, source_name)

    requested_format = format
    data = slot(start, stop).wait()

    content_type = 'application/octet-stream'
    if requested_format == 'raw':
        print('returning raw')
        stream = io.BytesIO(encode_raw(data))
        return Response(content=stream, content_type=content_type)

    if requested_format == 'npz':
        print('encoding')
        data = numpy.asarray(data, order='C')
        stream = encode_npz(data)
        return Response(content=stream, content_type=content_type)

@time_function_call(logger=logger)
def get_voxels(dataset_name: str, source_name: str, roi: RoiType) -> Response:
    print(dataset_name, source_name, roi['extents_min'], roi['extents_max'], roi['format'])
    start = map(int, roi['extents_min'].split('_'))
    stop = map(int, roi['extents_max'].split('_'))
    slot = get_current_app()._ilastik_api.slot_tracker.get_slot(dataset_name, source_name)

    requested_format = roi['format']
    # assert format == 'raw', "only raw for now"
    data = slot(start, stop).wait()

    content_type = 'application/octet-stream'
    if requested_format == 'raw':
        print('returning raw')
        stream = io.BytesIO(encode_raw(data))
        return Response(content=stream, content_type=content_type)

    if requested_format == 'npz':
        print('encoding')
        data = numpy.asarray(data, order='C')
        stream = encode_npz(data)
        return Response(content=stream, content_type=content_type)


@time_function_call(logger=logger)
def get_n5(dataset_name: str, source_name: str, t:int, c:int, z:int, y:int, x:int) -> Response:
    print(dataset_name, source_name, t,c,z,y,x)
    slot = get_current_app()._ilastik_api.slot_tracker.get_slot(dataset_name, source_name)
    n5_file_list = get_current_app()._n5_file_list
    n5_dataset = _lazy_n5_dataset_access(n5_file_list, dataset_name, source_name, slot)
    chunksize = np.array([1,1,64, 64, 64])
    start = chunksize * np.array([t, c, z, y, x])
    stop = np.minimum(chunksize * np.array([t+1, c+1, z+1, y+1, x+1]), slot.meta.shape)
    print(f"Got start {start} and stop {stop}")

    data = slot(start, stop).wait()

    n5_dataset.write_subarray(start, data)
    
    #read again from file:
    import os
    path = os.path.dirname(n5_dataset.attrs.path)
    path = os.path.join(path, str(t), str(c), str(z), str(y), str(x))
    stream = open(path, 'rb').read()

    content_type = 'application/octet-stream'
    return Response(content=stream, content_type=content_type)

def get_n5_attribs(dataset_name: str, source_name: str) -> Response:
    print("get attribs: ", dataset_name, source_name)
    slot = get_current_app()._ilastik_api.slot_tracker.get_slot(dataset_name, source_name)
    n5_file_list = get_current_app()._n5_file_list
    n5_dataset = _lazy_n5_dataset_access(n5_file_list, dataset_name, source_name, slot)
    print(f"Got N5 dataset at {n5_dataset.attrs.path}")
    stream = open(n5_dataset.attrs.path, 'rb').read()
    # open attribute.json of dataset and serve that
    return Response(content=stream, content_type='application/json')

def _lazy_n5_dataset_access(n5_file_list, dataset_name, source_name, slot):
    if dataset_name in n5_file_list:
        if source_name in n5_file_list[dataset_name]:
            return n5_file_list[dataset_name][source_name]
    else:
        n5_file_list[dataset_name] = {}

    # need to open new n5 file handle
    import tempfile
    tmpfile = tempfile.NamedTemporaryFile(delete=True)
    tmpfilename = tmpfile.name
    tmpfile.close()
    f = z5py.File(tmpfilename, False)
    dtype = np.dtype(slot.meta.dtype).name
    print(f"Creating dataset of shape {slot.meta.shape} and dtype {dtype}")
    ds = f.create_dataset('data', shape=slot.meta.shape, dtype=dtype, chunks=(1,1,64, 64, 64))
    return ds

def encode_npz(subvol):
    fileobj = io.BytesIO()
    if len(subvol.shape) == 3:
        subvol = numpy.expand_dims(subvol, 0)
    numpy.save(fileobj, subvol)
    cdz = zlib.compress(fileobj.getvalue())
    return cdz


def encode_raw(subvol):
    return subvol.tostring('C')
