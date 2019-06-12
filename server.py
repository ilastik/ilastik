from flask import Flask, request, send_file
from functools import partial
from threading import Thread
import io
import json
import os
from flask import Flask, flash, request, redirect, url_for
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
        obj = klass.from_json_data(cls.get_request_params())
        uid = uuid.uuid4()
        cls.objects[uid] = obj
        return obj, str(uid)

    @classmethod
    def get(cls, key):
        uid = uuid.UUID(str(key))
        return cls.objects[uid]

    @classmethod
    def get_request_params(cls):
        payload = {}
        for k, v in request.form.items():
            try:
                payload[k] = cls.get(v)
            except (ValueError, KeyError):
                payload[k] = v
        for k, v in request.files.items():
            payload[k] = v.read()
        return listify(unflatten(payload))

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
    classifier = Context.get(request.args['pixel_classifier_id'])
    roi_params = {}
    for axis, v in request.args.items():
        if axis in 'tcxyz':
            start, stop = tuple(int(part) for part in v.split('_'))
            roi_params[axis] = slice(start, stop)
    roi = Slice5D(**roi_params)
    data_source = Context.get(request.args['data_source_id']).resize(roi)
    channel = int(request.args.get('channel', 0))
    predictions, _ = classifier.predict(data_source)

    out_image = predictions.as_pil_images()[channel]
    out_file = io.BytesIO()
    out_image.save(out_file, 'png')
    out_file.seek(0)
    return send_file(out_file, mimetype='image/png')


Thread(target=partial(app.run, host='0.0.0.0')).start()
