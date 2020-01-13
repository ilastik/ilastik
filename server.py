from concurrent.futures import ThreadPoolExecutor
from functools import partial
from threading import Thread
from typing import Dict, List, Tuple, Optional, Hashable
import io
import json
import os
import flask
from flask import Flask, request, Response, send_file
from flask_cors import CORS
import uuid
import numpy as np
import urllib
from PIL import Image as PilImage
import argparse
from pathlib import Path

from ndstructs import Point5D, Slice5D, Shape5D, Array5D
from ndstructs.datasource import DataSource
from ilastik.annotations import Annotation, Scribblings
from ilastik.classifiers.pixel_classifier import PixelClassifier, StrictPixelClassifier, Predictions
from ndstructs.datasource import PilDataSource
from ilastik.features.feature_extractor import FeatureExtractor
from ilastik.features.fastfilters import (
    GaussianSmoothing,
    HessianOfGaussianEigenvalues,
    GaussianGradientMagnitude,
    LaplacianOfGaussian,
    DifferenceOfGaussians,
    StructureTensorEigenvalues
)
from ilastik.features.vigra_features import GaussianSmoothing, HessianOfGaussian
from ilastik.utility import flatten, unflatten, listify

parser = argparse.ArgumentParser(description='Runs ilastik prediction web server')
parser.add_argument('--host', default='localhost', help='ip or hostname where the server will listen')
parser.add_argument('--port', default=5000, type=int, help='port to listen on')
parser.add_argument('--ngurl', default='http://localhost:8080', help='url where neuroglancer is being served')
parser.add_argument('--sample-dirs', type=Path, help='List of directories containing n5 samples', nargs='+')
args = parser.parse_args()

#FIXME:Rasterizing should probabl be done on the client
class NgAnnotation(Annotation):
    def __init__(self, color: Tuple[int, int, int], voxels: List[Point5D], raw_data:DataSource):
        self.color = tuple(color) #FIXME: JSonSerializable only produces list on iterables
        self.voxels = [Point5D.from_json_data(coords) for coords in voxels]

        hashed_color = hash(self.color) % 255

        min_point = Point5D(**{key: min(vox[key] for vox in self.voxels) for key in 'xyz'})
        max_point = Point5D(**{key: max(vox[key] for vox in self.voxels) for key in 'xyz'})

        # +1 because slice.stop is exclusive, but pointA and pointB are inclusive
        scribbling_roi = Slice5D.zero(**{key: slice(min_point[key],  max_point[key] + 1) for key in 'xyz'})
        scribblings = Scribblings.allocate(scribbling_roi, dtype=np.uint8, value=0)

        for voxel in self.voxels:
            colored_point = Scribblings.allocate(Slice5D.zero().translated(voxel), dtype=np.uint8, value=hashed_color)
            scribblings.set(colored_point)

        super().__init__(scribblings=scribblings, raw_data=raw_data)


feature_extractor_classes = [
    FeatureExtractor, #this allows one to GET /feature_extractor and get a list of all created feature extractors
    GaussianSmoothing,
    HessianOfGaussianEigenvalues,
    GaussianGradientMagnitude,
    LaplacianOfGaussian,
    DifferenceOfGaussians,
    StructureTensorEigenvalues,
]

workflow_classes = {klass.__name__: klass for klass in [PixelClassifier, DataSource, Annotation, NgAnnotation] + feature_extractor_classes}

app = Flask("WebserverHack")
CORS(app)


class Context:
    objects = {}

    @classmethod
    def do_rpc(cls):
        request_payload = cls.get_request_payload()
        obj = cls.load(request_payload.pop('self'))

    @classmethod
    def get_class_named(cls, name:str):
        name = name if name in workflow_classes else name.title().replace('_', '')
        return workflow_classes[name]

    @classmethod
    def create(cls, klass):
        request_payload = cls.get_request_payload()
        obj = klass.from_json_data(request_payload)
        key = cls.store(request_payload.get('id'), obj)
        return obj, key

    @classmethod
    def load(cls, key):
        return cls.objects[key]

    @classmethod
    def store(cls, obj_id:Optional[Hashable], obj):
        obj_id = obj_id if obj_id is not None else uuid.uuid4()
        key = f"pointer@{obj_id}"
        cls.objects[key] = obj
        return key

    @classmethod
    def remove(cls, klass: type, key):
        target_class = cls.objects[key].__class__
        if not issubclass(target_class, klass):
            raise Exception(f"Unexpected class {target_class} when deleting object with key {key}")
        return cls.objects.pop(key)

    @classmethod
    def get_request_payload(cls):
        payload = {}
        for k, v in request.form.items():
            if isinstance(v, str) and v.startswith('pointer@'):
                payload[k] = cls.load(v)
            else:
                payload[k] = v
        for k, v in request.files.items():
            payload[k] = v.read()
        return listify(unflatten(payload))

    @classmethod
    def get_all(cls, klass) -> Dict[str, object]:
        return {key: obj for key, obj in cls.objects.items() if isinstance(obj, klass)}

def do_predictions(roi:Slice5D, classifier_id:str, datasource_id:str) -> Predictions:
    classifier = Context.load(classifier_id)
    full_data_source = Context.load(datasource_id)
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

@app.route('/predict/', methods=['GET'])
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
def ng_predict(classifier_id:str, datasource_id:str, xBegin:int, xEnd:int, yBegin:int, yEnd:int, zBegin:int, zEnd:int):
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
    classifier = Context.load(classifier_id)
    datasource = Context.load(datasource_id)

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
                "voxel_offset": [0,0,0],
                "chunk_sizes": [datasource.tile_shape.to_tuple('xyz')],
                "encoding": "raw",
            },
        ],
    })
    return resp

@app.route('/datasource/<datasource_id>/data/<int:xBegin>-<int:xEnd>_<int:yBegin>-<int:yEnd>_<int:zBegin>-<int:zEnd>')
def ng_raw(datasource_id:str, xBegin:int, xEnd:int, yBegin:int, yEnd:int, zBegin:int, zEnd:int):
    requested_roi = Slice5D(x=slice(xBegin, xEnd), y=slice(yBegin, yEnd), z=slice(zBegin, zEnd))
    datasource = Context.load(datasource_id)
    data = datasource.resize(requested_roi).retrieve()

    resp = flask.make_response(data.raw('xyzc').tobytes('F'))
    resp.headers['Content-Type'] = 'application/octet-stream'
    return resp

def get_sample_datasets() -> List[Dict]:
    rgb_shader = """void main() {
      emitRGB(vec3(
        toNormalized(getDataValue(0)),
        toNormalized(getDataValue(1)),
        toNormalized(getDataValue(2))
      ));
    }
    """

    protocol = request.headers.get('X-Forwarded-Protocol', 'http')
    host = request.headers.get('X-Forwarded-Host', args.host)
    port = '' if 'X-Forwarded-Host' in request.headers else f':{args.port}'
    prefix = request.headers.get('X-Forwarded-Prefix', '/')

    links = []
    for datasource_id, datasource in Context.get_all(DataSource).items():
        url_data = {
            "layers": [
                {
                "source": f"precomputed://{protocol}://{host}{port}{prefix}datasource/{datasource_id}",
                "type": "image",
                "blend": "default",
                "shader": rgb_shader,
                "shaderControls": {},
                "name": datasource.name
                },
                {
                    "type": "annotation",
                    "annotations": [],
                    "voxelSize": [
                        1,
                        1,
                        1
                    ],
                    "name": "annotation"
                }
            ],
            "navigation": {
                "zoomFactor": 1
            },
            "selectedLayer": {
                "layer": "annotation",
                "visible": True
            },
            "layout": "4panel"
        }
        yield {
            'url': f"{args.ngurl}#!" + urllib.parse.quote(str(json.dumps(url_data))),
            'name': datasource.name
        }

@app.route('/datasets')
def get_datasets():
    return flask.jsonify(list(get_sample_datasets()))

@app.route('/neuroglancer-samples')
def ng_samples():
    link_tags = [f'<a href="{sample["url"]}">{sample["name"]}</a><br/>' for sample in get_sample_datasets()]
    links = '\n'.join(link_tags)
    return f"""
        <html>
            <head>
                <meta charset="UTF-8">
                <link rel=icon href="https://www.ilastik.org/assets/ilastik-logo.png">
            </head>

            <body>
                {links}
            </body>
        </html>
    """



@app.route('/datasource/<datasource_id>/info')
def datasource_info_dict(datasource_id:str) -> Dict:
    datasource = Context.load(datasource_id)

    resp = flask.jsonify({
        "@type": "neuroglancer_multiscale_volume",
        "type": "image",
        "data_type": "uint8", #DONT FORGET TO CONVERT PREDICTIONS TO UINT8!
        "num_channels": int(datasource.full_shape.c),
        "scales": [
            {
                "key": "data",
                "size": [int(v) for v in datasource.full_shape.to_tuple('xyz')],
                "resolution": [1,1,1],
                "voxel_offset": [0,0,0],
                "chunk_sizes": [datasource.tile_shape.to_tuple('xyz')],
                "encoding": "raw",
            },
        ],
    })
    return resp

@app.route('/<class_name>/<object_id>', methods=['DELETE'])
def remove_object(class_name, object_id:str):
    Context.remove(Context.get_class_named(class_name), object_id)
    return flask.jsonify({'id': object_id})

@app.route("/<class_name>/", methods=['POST'])
def create_object(class_name:str):
    obj, uid = Context.create(Context.get_class_named(class_name))
    return json.dumps(uid)

@app.route('/<class_name>/', methods=['GET'])
def list_objects(class_name):
    klass = Context.get_class_named(class_name)
    return flask.jsonify({ext_id: ext.json_data for ext_id, ext in Context.get_all(klass).items()})

@app.route('/<class_name>/<object_id>', methods=['GET'])
def show_object(class_name:str, object_id:str):
    klass = Context.get_class_named(class_name)
    return flask.jsonify(Context.load(object_id).json_data)

for sample_dir in args.sample_dirs:
    for sample_file in sample_dir.iterdir():
        if sample_file.is_dir() and sample_file.suffix in ('.n5', '.N5'):
            for dataset in sample_file.iterdir():
                if dataset.is_dir():
                    datasource = DataSource.create(dataset.absolute().as_posix())
                    print(f"---->> Adding sample {datasource.name}")
                    Context.store(None, datasource)

app.run(host=args.host, port=args.port)
