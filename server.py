from flask import Flask, request
from threading import Thread
import json
import os
from flask import Flask, flash, request, redirect, url_for

from ilastik.array5d.point5D import Point5D, Slice5D, Shape5D
from ilastik.array5d import Array5D
from ilastik.annotations import Annotation
from ilastik.classifiers.pixel_classifier import PixelClassifier, StrictPixelClassifier
from ilastik.data_source import FlatDataSource
from ilastik.features.vigra_features import GaussianSmoothing, HessianOfGaussian

app = Flask("WebserverHack")
app.config['DATA_DIR'] = '/tmp/flask_stuff/'
app.config['AVAILABLE_FEATURE_EXTRACTORS'] = [GaussianSmoothing, HessianOfGaussian]
app.config['FEATURE_EXTRACTOR_MAP'] = {f.__name__:f for f in app.config['AVAILABLE_FEATURE_EXTRACTORS']}


os.system(f"rm -rfv {app.config['DATA_DIR']}")
os.system(f"mkdir -v {app.config['DATA_DIR']}")

data_sources = {}
annotations = {}
classifiers = {}
feature_extractors = {}


from inspect import signature
from abc import ABC, abstractmethod

class RequestData(dict):
    def __init__(self, req):
        for k, v in req.files.items():
            path = os.path.join(app.config['DATA_DIR'], v.filename)
            v.save(path)
            self[k] = path
        for k, v in req.form.items():
            assert k not in self
            self[k] = json.loads(v)

class WebAnnotation(Annotation):
    @classmethod


def get_list_value_from_request(key:str, permissive:bool=True):
    value = json.loads(request.form.get(key))
    if not isinstance(value, list):
        return [value]
    return value

@app.route('/data_sources', methods=['POST'])
def create_data_source():
    path = create_file_from_request('raw_data')
    data_source =  FlatDataSource(path)
    data_source_id = str(id(data_source))
    data_sources[data_source_id] = data_source
    return data_source_id

@app.route('/annotations', methods=['POST'])
def create_annotation(cls, raw_data:'FileStorage', data_source_id:str, location:dict):
    path = create_file_from_request('raw_data')
    data_source = data_sources[request.form.get('data_source_id')]
    location = Point5D.from_json(request.form.get('location'))
    annotation = Annotation.from_png(path, raw_data=data_source, location=location)
    annotation_id = str(id(data_source))
    annotations[annotation_id] = annotation
    return annotation_id

@app.route('/feature_extractors', methods=['GET'])
def list_feature_extractors():
    return json.dumps({extractor_id:extractor.json_data for extractor_id, extractor in feature_extractors.items()})

@app.route('/feature_extractors/<class_name>', methods=['POST'])
def create_feature_extractor(class_name:str):
    extractor_class = app.config['FEATURE_EXTRACTOR_MAP'][class_name.title().replace('_', '')]
    extractor = extractor_class.from_json(request.form.get('extractor_params'))
    extractor_id = str(hash(extractor))
    if extractor_id not in feature_extractors:
        feature_extractors[extractor_id] = extractor
    return extractor_id

@app.route('/pixel_classifier', methods=['POST'])
def create_classifier():
    print(f"==================>>>> {request.form.get('annotation_ids')}")
    annotation_ids = get_list_value_from_request('annotation_ids')
    selected_annotations = tuple(annotations[i] for i in annotation_ids)

    extractor_ids = get_list_value_from_request('feature_extractor_ids')
    selected_extractors = tuple(feature_extractors[i] for i in extractor_ids)

    extractor = FeatureExtractorCollection.get(selected_extractors)
    classifier = StrictPixelClassifier.get(extractor, selected_annotations)
    return str(id(classifier))

@app.route('/predictions/')
def predict():
    pass

Thread(target=app.run).start()
