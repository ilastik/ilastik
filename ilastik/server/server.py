from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor
import io
import json
import flask
from flask import Flask, request, Response, send_file
from flask_cors import CORS
import urllib
from PIL import Image as PilImage
import argparse
from pathlib import Path

from ndstructs import Point5D, Slice5D, Shape5D, Array5D
from ndstructs.datasource import DataSource, DataSourceSlice, SequenceDataSource
from ndstructs.utils import JsonSerializable, from_json_data

from ilastik.workflows.pixelClassification.pixel_classification_workflow_2 import PixelClassificationWorkflow2
from ilastik.server.pixel_classification_web_adapter import PixelClassificationWorkflow2WebAdapter
from ilastik.features.feature_extractor import FeatureDataMismatchException
from ilastik.classifiers.pixel_classifier import Predictions
from ilastik.server.WebContext import WebContext, EntityNotFoundException

parser = argparse.ArgumentParser(description="Runs ilastik prediction web server")
parser.add_argument("--host", default="localhost", help="ip or hostname where the server will listen")
parser.add_argument("--port", default=5000, type=int, help="port to listen on")
parser.add_argument("--ngurl", default="http://localhost:8080", help="url where neuroglancer is being served")
parser.add_argument("--sample-dirs", type=Path, help="List of directories containing n5 samples", nargs="+")
args = parser.parse_args()

app = Flask("WebserverHack")
CORS(app)


@app.route("/PixelClassificationWorkflow2/<pix_workflow_id>/add_ilp_feature_extractors", methods=["POST"])
def add_ilp_feature_extractors(pix_workflow_id: str):
    workflow = WebContext.load(pix_workflow_id)
    adapter = PixelClassificationWorkflow2WebAdapter(web_context=WebContext, workflow=workflow)
    payload = WebContext.get_request_payload()
    extractors = []
    for extractor_spec in payload:
        extractor_class = WebContext.get_class_named(extractor_spec.pop("name"))
        extractor = from_json_data(extractor_class.from_ilp_scale, extractor_spec)
        extractors.append(extractor)
    return adapter.add_feature_extractors(extractors)


@app.route("/PixelClassificationWorkflow2/<pix_workflow_id>/<method_name>", methods=["GET", "POST", "DELETE"])
def run_pixel_classification_workflow_method(pix_workflow_id: str, method_name: str):
    if (
        request.method == "POST"
        and method_name not in ("add_annotations", "add_feature_extractors", "upload_to_cloud_ilastik")
        or request.method == "DELETE"
        and method_name not in ("remove_annotations", "remove_feature_extractors", "clear_feature_extractors")
        or request.method == "GET"
        and method_name not in ("get_classifier", "ilp_project")
    ):
        return flask.Response(f"Can't call method {method_name} on pixel classification workflow", status=403)
    return do_run_pixel_classification_workflow_method(pix_workflow_id, method_name)


def do_run_pixel_classification_workflow_method(pix_workflow_id: str, method_name: str):
    workflow = WebContext.load(pix_workflow_id)
    if not isinstance(workflow, PixelClassificationWorkflow2):
        return flask.Response(f"Could not find PixelClassificationWorkflow2 with id {pix_workflow_id}", status=404)
    adapter = PixelClassificationWorkflow2WebAdapter(workflow=workflow, web_context=WebContext)
    payload = WebContext.get_request_payload()
    return from_json_data(getattr(adapter, method_name), payload)


def do_predictions(roi: Slice5D, classifier_id: str, datasource_id: str) -> Predictions:
    classifier = WebContext.load(classifier_id)
    datasource = WebContext.load(datasource_id)
    backed_roi = DataSourceSlice(datasource, **roi.to_dict()).defined()

    predictions = classifier.allocate_predictions(backed_roi)
    # with ThreadPoolExecutor() as executor:
    for raw_tile in backed_roi.get_tiles():

        def predict_tile(tile):
            tile_prediction = classifier.predict(tile)
            predictions.set(tile_prediction, autocrop=True)

        predict_tile(raw_tile)
        # executor.submit(predict_tile, raw_tile)
    return predictions


@app.route("/predict/", methods=["GET"])
def predict():
    roi_params = {}
    for axis, v in request.args.items():
        if axis in "tcxyz":
            start, stop = [int(part) for part in v.split("_")]
            roi_params[axis] = slice(start, stop)

    predictions = do_predictions(
        roi=Slice5D(**roi_params),
        classifier_id=request.args["pixel_classifier_id"],
        datasource_id=request.args["data_source_id"],
    )

    channel = int(request.args.get("channel", 0))
    data = predictions.cut(Slice5D(c=channel)).as_uint8(normalized=True).raw("yx")
    out_image = PilImage.fromarray(data)
    out_file = io.BytesIO()
    out_image.save(out_file, "png")
    out_file.seek(0)
    return send_file(out_file, mimetype="image/png")


# https://github.com/google/neuroglancer/tree/master/src/neuroglancer/datasource/precomputed#unsharded-chunk-storage
@app.route(
    "/predictions/<classifier_id>/<datasource_id>/data/<int:xBegin>-<int:xEnd>_<int:yBegin>-<int:yEnd>_<int:zBegin>-<int:zEnd>"
)
def ng_predict(
    classifier_id: str, datasource_id: str, xBegin: int, xEnd: int, yBegin: int, yEnd: int, zBegin: int, zEnd: int
):
    requested_roi = Slice5D(x=slice(xBegin, xEnd), y=slice(yBegin, yEnd), z=slice(zBegin, zEnd))
    predictions = do_predictions(roi=requested_roi, classifier_id=classifier_id, datasource_id=datasource_id)

    # https://github.com/google/neuroglancer/tree/master/src/neuroglancer/datasource/precomputed#raw-chunk-encoding
    # "(...) data for the chunk is stored directly in little-endian binary format in [x, y, z, channel] Fortran order"
    resp = flask.make_response(predictions.as_uint8().raw("xyzc").tobytes("F"))
    resp.headers["Content-Type"] = "application/octet-stream"
    return resp


@app.route("/predictions/<classifier_id>/<datasource_id>/info/")
def info_dict(classifier_id: str, datasource_id: str) -> Dict:
    classifier = WebContext.load(classifier_id)
    datasource = WebContext.load(datasource_id)

    expected_predictions_shape = classifier.get_expected_roi(datasource.roi).shape

    resp = flask.jsonify(
        {
            "@type": "neuroglancer_multiscale_volume",
            "type": "image",
            "data_type": "uint8",  # DONT FORGET TO CONVERT PREDICTIONS TO UINT8!
            "num_channels": int(expected_predictions_shape.c),
            "scales": [
                {
                    "key": "data",
                    "size": [int(v) for v in expected_predictions_shape.to_tuple("xyz")],
                    "resolution": [1, 1, 1],
                    "voxel_offset": [0, 0, 0],
                    "chunk_sizes": [datasource.tile_shape.to_tuple("xyz")],
                    "encoding": "raw",
                }
            ],
        }
    )
    return resp


@app.route("/predictions/<classifier_id>/neuroglancer_shader", methods=["GET"])
def get_predictions_shader(classifier_id: str):
    classifier = WebContext.load(classifier_id)

    color_lines: List[str] = []
    colors_to_mix: List[str] = []

    for idx, color in enumerate(classifier.color_map.keys()):
        color_line = (
            f"vec3 color{idx} = (vec3({color.r}, {color.g}, {color.b}) / 255.0) * toNormalized(getDataValue({idx}));"
        )
        color_lines.append(color_line)
        colors_to_mix.append(f"color{idx}")

    shader_lines = [
        "void main() {",
        "    " + "\n    ".join(color_lines),
        "    emitRGBA(",
        f"        vec4({' + '.join(colors_to_mix)}, 1.0)",
        "    );",
        "}",
    ]
    return flask.Response("\n".join(shader_lines), mimetype="text/plain")


@app.route("/datasource/<datasource_id>/data/<int:xBegin>-<int:xEnd>_<int:yBegin>-<int:yEnd>_<int:zBegin>-<int:zEnd>")
def ng_raw(datasource_id: str, xBegin: int, xEnd: int, yBegin: int, yEnd: int, zBegin: int, zEnd: int):
    requested_roi = Slice5D(x=slice(xBegin, xEnd), y=slice(yBegin, yEnd), z=slice(zBegin, zEnd))
    datasource = WebContext.load(datasource_id)
    data = datasource.retrieve(requested_roi)

    resp = flask.make_response(data.raw("xyzc").tobytes("F"))
    resp.headers["Content-Type"] = "application/octet-stream"
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

    grayscale_shader = """void main() {
      emitGrayscale(toNormalized(getDataValue(0)));
    }
    """

    protocol = request.headers.get("X-Forwarded-Proto", "http")
    host = request.headers.get("X-Forwarded-Host", args.host)
    port = "" if "X-Forwarded-Host" in request.headers else f":{args.port}"
    prefix = request.headers.get("X-Forwarded-Prefix", "/")

    links = []
    for datasource_id, datasource in WebContext.get_all(DataSource).items():
        url_data = {
            "layers": [
                {
                    "source": f"precomputed://{protocol}://{host}{port}{prefix}datasource/{datasource_id}",
                    "type": "image",
                    "blend": "default",
                    "shader": grayscale_shader if datasource.shape.c == 1 else rgb_shader,
                    "shaderControls": {},
                    "name": datasource.name,
                },
                {"type": "annotation", "annotations": [], "voxelSize": [1, 1, 1], "name": "annotation"},
            ],
            "navigation": {"zoomFactor": 1},
            "selectedLayer": {"layer": "annotation", "visible": True},
            "layout": "xy",
        }
        yield {"url": f"{args.ngurl}#!" + urllib.parse.quote(str(json.dumps(url_data))), "name": datasource.name}


@app.route("/datasets")
def get_datasets():
    return flask.jsonify(list(get_sample_datasets()))


@app.route("/neuroglancer-samples")
def ng_samples():
    link_tags = [f'<a href="{sample["url"]}">{sample["name"]}</a><br/>' for sample in get_sample_datasets()]
    links = "\n".join(link_tags)
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


@app.route("/datasource/<datasource_id>/info")
def datasource_info_dict(datasource_id: str) -> Dict:
    datasource = WebContext.load(datasource_id)

    resp = flask.jsonify(
        {
            "@type": "neuroglancer_multiscale_volume",
            "type": "image",
            "data_type": "uint8",  # DONT FORGET TO CONVERT PREDICTIONS TO UINT8!
            "num_channels": int(datasource.shape.c),
            "scales": [
                {
                    "key": "data",
                    "size": [int(v) for v in datasource.shape.to_tuple("xyz")],
                    "resolution": [1, 1, 1],
                    "voxel_offset": [0, 0, 0],
                    "chunk_sizes": [datasource.tile_shape.to_tuple("xyz")],
                    "encoding": "raw",
                }
            ],
        }
    )
    return resp


@app.route("/<class_name>/<object_id>", methods=["DELETE"])
def remove_object(class_name, object_id: str):
    WebContext.remove(WebContext.get_class_named(class_name), object_id)
    return flask.jsonify({"id": object_id})


@app.errorhandler(FeatureDataMismatchException)
def handle_feature_data_mismatch(error):
    return flask.Response(str(error), status=400)


@app.errorhandler(EntityNotFoundException)
def handle_feature_data_mismatch(error):
    return flask.Response(str(error), status=404)


@app.route("/<class_name>/", methods=["POST"])
def create_object(class_name: str):
    obj, uid = WebContext.create(WebContext.get_class_named(class_name))
    return json.dumps(uid)


@app.route("/<class_name>/", methods=["GET"])
def list_objects(class_name):
    klass = WebContext.get_class_named(class_name)
    return flask.Response(JsonSerializable.jsonify(WebContext.get_all(klass)), mimetype="application/json")


@app.route("/<class_name>/<object_id>", methods=["GET"])
def show_object(class_name: str, object_id: str):
    klass = WebContext.get_class_named(class_name)
    obj = WebContext.load(object_id)
    payload = obj.to_json_data(referencer=WebContext.referencer)
    return flask.jsonify(payload)


for sample_dir in args.sample_dirs or ():
    for sample_file in sample_dir.iterdir():
        if sample_file.is_dir() and sample_file.suffix in (".n5", ".N5"):
            for dataset in sample_file.iterdir():
                if dataset.is_dir():
                    datasource = DataSource.create(dataset.absolute())
                    print(f"---->> Adding sample {datasource.name}")
                    WebContext.store(datasource)

app.run(host=args.host, port=args.port)
