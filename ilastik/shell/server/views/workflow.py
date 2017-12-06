from apistar import get_current_app, Response
from ..tools import log_function_call, time_function_call
from ..ilastikAPItypes import RoiType
import io

import logging
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


def encode_npz(subvol):
    fileobj = io.BytesIO()
    if len(subvol.shape) == 3:
        subvol = numpy.expand_dims(subvol, 0)
    numpy.save(fileobj, subvol)
    cdz = zlib.compress(fileobj.getvalue())
    return cdz


def encode_raw(subvol):
    return subvol.tostring('C')
