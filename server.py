from concurrent.futures import ThreadPoolExecutor
from functools import partial
from threading import Thread
from typing import Dict
import io
import json
import os
import flask
from flask import Flask, request, Response, send_file
from flask_cors import CORS
import uuid
import numpy as np
from PIL import Image as PilImage

from ndstructs import Point5D, Slice5D, Shape5D, Array5D
from ilastik.annotations import Annotation
from ilastik.classifiers.pixel_classifier import PixelClassifier, StrictPixelClassifier, Predictions
from ndstructs.datasource import PilDataSource
from ilastik.features.vigra_features import GaussianSmoothing, HessianOfGaussian
from ilastik.utility import flatten, unflatten, listify

app = Flask("WebserverHack")
CORS(app)
app.config['DATA_DIR'] = '/tmp/flask_stuff/'
app.config['AVAILABLE_FEATURE_EXTRACTORS'] = [GaussianSmoothing, HessianOfGaussian]
app.config['FEATURE_EXTRACTOR_MAP'] = {f.__name__:f for f in app.config['AVAILABLE_FEATURE_EXTRACTORS']}


os.system(f"rm -rfv {app.config['DATA_DIR']}")
os.system(f"mkdir -v {app.config['DATA_DIR']}")

files = {}
data_sources = {}
annotations = {}
classifiers = {}
feature_extractors = {}

class Context:
    objects = {}

    @classmethod
    def create(cls, klass):
        request_payload = cls.get_request_payload()
        obj = klass.from_json_data(request_payload)
        uid = request_payload.get('id', str(uuid.uuid4()))
        cls.set(uid, obj)
        return obj, str(uid)

    @classmethod
    def get(cls, key):
        return cls.objects[key]

    @classmethod
    def set(cls, obj_id, obj):
        cls.objects[obj_id] = obj

    @classmethod
    def remove(cls, key):
        return cls.objects.pop(key)

    @classmethod
    def get_request_payload(cls):
        payload = {}
        for k, v in request.form.items():
            try:
                payload[k] = cls.get(v)
            except (ValueError, KeyError):
                payload[k] = v
        for k, v in request.files.items():
            payload[k] = v.read()
        return listify(unflatten(payload))


@app.route('/lines', methods=['POST'])
def create_line_annotation():
    request_payload = Context.get_request_payload()
    print(f"Got this payload: ", json.dumps(request_payload, indent=4))
    resp = Response("got it!!!!")
    return resp

@app.route('/lines/<line_id>', methods=['DELETE'])
def remove_line_annotation(line_id:str):
    print(f"Deleting {line_id}..........")
    #Context.remove(line_id)
    resp = Response("deleted it!!!!")
    return resp

@app.route('/data_sources', methods=['POST'])
def create_data_source():
    _, uid = Context.create(PilDataSource)
    return json.dumps(uid)

@app.route('/annotations', methods=['POST'])
def create_annotation():
    _, uid = Context.create(Annotation)
    return json.dumps(uid)

@app.route('/feature_extractors/<class_name>', methods=['POST'])
def create_feature_extractor(class_name:str):
    extractor_class = app.config['FEATURE_EXTRACTOR_MAP'][class_name.title().replace('_', '')]
    _, uid = Context.create(extractor_class)
    return json.dumps(uid)

@app.route('/pixel_classifier', methods=['POST'])
def create_classifier():
    _, uid = Context.create(PixelClassifier)
    return json.dumps(uid)

def do_predictions(roi:Slice5D, classifier_id:str, datasource_id:str) -> Predictions:
    classifier = Context.get(classifier_id)
    full_data_source = Context.get(datasource_id)
    clamped_roi = roi.clamped(full_data_source)
    data_source = full_data_source.resize(clamped_roi)

    predictions = classifier.allocate_predictions(data_source)
    with ThreadPoolExecutor() as executor:
        for raw_tile in data_source.get_tiles():
            def predict_tile(tile):
                tile_prediction, tile_features = classifier.predict(tile)
                predictions.set(tile_prediction, autocrop=True)
            executor.submit(predict_tile, raw_tile)
    return predictions

@app.route('/pixel_predictions/', methods=['GET'])
def predict():
    roi_params = {}
    for axis, v in request.args.items():
        if axis in 'tcxyz':
            start, stop = [int(part) for part in v.split('_')]
            roi_params[axis] = slice(start, stop)

    predictions = do_predictions(roi=Slice5D(**roi_params),
                                 classifier_id=request.args['pixel_classifier_id'],
                                 datasource_id=request.args['data_source_id'])

    channel=int(request.args.get('channel', 0))
    out_image = predictions.as_pil_images()[channel]
    out_file = io.BytesIO()
    out_image.save(out_file, 'png')
    out_file.seek(0)
    return send_file(out_file, mimetype='image/png')

#https://github.com/google/neuroglancer/tree/master/src/neuroglancer/datasource/precomputed#unsharded-chunk-storage
@app.route('/predictions/<classifier_id>/<datasource_id>/data/<int:xBegin>-<int:xEnd>_<int:yBegin>-<int:yEnd>_<int:zBegin>-<int:zEnd>')
def ngpredict(classifier_id:str, datasource_id:str, xBegin:int, xEnd:int, yBegin:int, yEnd:int, zBegin:int, zEnd:int):
    requested_roi = Slice5D(x=slice(xBegin, xEnd), y=slice(yBegin, yEnd), z=slice(zBegin, zEnd))
    predictions = do_predictions(roi=requested_roi,
                                 classifier_id=classifier_id,
                                 datasource_id=datasource_id)

    # https://github.com/google/neuroglancer/tree/master/src/neuroglancer/datasource/precomputed#raw-chunk-encoding
    # "(...) data for the chunk is stored directly in little-endian binary format in [x, y, z, channel] Fortran order"
    resp = flask.make_response(predictions.as_uint8().raw('xyzc').tobytes('F'))
    resp.headers['Content-Type'] = 'application/octet-stream'
    return resp

@app.route('/predictions/<classifier_id>/<datasource_id>/info')
def info_dict(classifier_id:str, datasource_id:str) -> Dict:
    classifier = Context.get(classifier_id)
    datasource = Context.get(datasource_id)

    expected_predictions_shape = classifier.get_expected_roi(datasource).shape

    resp = flask.jsonify({
        "@type": "neuroglancer_multiscale_volume",
        "type": "image",
        "data_type": "uint8", #DONT FORGET TO CONVERT PREDICTIONS TO UINT8!
        "num_channels": int(expected_predictions_shape.c),
        "scales": [
            {
                "key": "data",
                "size": [int(v) for v in expected_predictions_shape.to_tuple('xyz')],
                "resolution": [1,1,1],
                "chunk_sizes": [[64, 64, 64]],
                "encoding": "raw",
            },
        ],
    })
    return resp




#Thread(target=partial(app.run, host='0.0.0.0')).start()
Thread(target=app.run).start()
