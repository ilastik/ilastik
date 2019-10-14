from concurrent.futures import ThreadPoolExecutor
from flask import Flask, request, send_file
from functools import partial
from threading import Thread
import io
import json
import os
from flask import Flask, flash, request, redirect, url_for, Response
import uuid
import numpy as np
from PIL import Image as PilImage

from ilastik.array5d.point5D import Point5D, Slice5D, Shape5D
from ilastik.array5d import Array5D
from ilastik.annotations import Annotation
from ilastik.classifiers.pixel_classifier import PixelClassifier, StrictPixelClassifier
from ilastik.data_source import FlatDataSource
from ilastik.features.vigra_features import GaussianSmoothing, HessianOfGaussian
from ilastik.utility import flatten, unflatten, listify

app = Flask("WebserverHack")
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
        uid = request_payload.get('id', uuid.uuid4())
        cls.set(uid, obj)
        return obj, str(uid)

    @classmethod
    def get(cls, key):
        uid = uuid.UUID(str(key))
        return cls.objects[uid]

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


@app.route('/lines', methods=['OPTIONS'])
def lines_endpoint_options(*args, **kwargs):
    resp = Response("allow, dang it")
    resp.headers['Access-Control-Allow-Origin'] = '*'
    resp.headers['Access-Control-Allow-Methods'] = '*'
    return resp

app.route('/lines/<line_id>', methods=['OPTIONS'])(lines_endpoint_options)

@app.route('/lines', methods=['POST'])
def create_line_annotation():
    request_payload = Context.get_request_payload()
    print(f"Got this payload: ", json.dumps(request_payload, indent=4))
    resp = Response("got it!!!!")
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp

@app.route('/lines/<line_id>', methods=['DELETE'])
def remove_line_annotation(line_id:str):
    print(f"Deleting {line_id}..........")
    #Context.remove(line_id)
    resp = Response("deleted it!!!!")
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp




@app.route('/data_sources', methods=['POST'])
def create_data_source():
    _, uid = Context.create(FlatDataSource)
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

@app.route('/pixel_predictions/', methods=['GET'])
def predict():
    roi_params = {}
    for axis, v in request.args.items():
        if axis in 'tcxyz':
            start, stop = tuple(int(part) for part in v.split('_'))
            roi_params[axis] = slice(start, stop)
    roi = Slice5D(**roi_params)
    classifier = Context.get(request.args['pixel_classifier_id'])
    data_source = Context.get(request.args['data_source_id']).resize(roi)
    channel = int(request.args.get('channel', 0))

    predictions = classifier.allocate_predictions(data_source)
    with ThreadPoolExecutor() as executor:
        for raw_tile in data_source.get_tiles():
            def predict_tile(raw_tile):
                tile_prediction, tile_features = classifier.predict(raw_tile)
                predictions.set(tile_prediction, autocrop=True)
            executor.submit(predict_tile, raw_tile)

    out_image = predictions.as_pil_images()[channel]
    out_file = io.BytesIO()
    out_image.save(out_file, 'png')
    out_file.seek(0)
    return send_file(out_file, mimetype='image/png')


#Thread(target=partial(app.run, host='0.0.0.0')).start()
Thread(target=app.run).start()
