import requests
import json
import numpy
from ilastik.utility import flatten, unflatten, listify
from ndstructs import Array5D
import os
import time


def post(*args, **kwargs):
    return send("post", *args, **kwargs)


def get(*args, **kwargs):
    return send("get", *args, **kwargs)


def send(method: str, *args, **kwargs):
    resp = getattr(requests, method)(*args, **kwargs)
    if resp.status_code != 200:
        raise Exception(resp.text)
    return resp


resp = post("http://localhost:5000/PixelClassificationWorkflow2/", data={})
workflow_id = resp.json()

resp = post(
    "http://localhost:5000/SkimageDataSource/",
    data={"path": "/home/tomaz/ilastikTests/SampleData/c_cells/cropped/cropped1.png"},
)
_data_source_id = resp.json()

precomputed_url = (f"precomputed://http://localhost:5000/datasource/{_data_source_id}/data",)
resp = post(
    f"http://localhost:5000/PixelClassificationWorkflow2/{workflow_id}/add_lane_for_url", data={"url": precomputed_url}
)
lane_id = resp.json()


resp = get(f"http://localhost:5000/data_source/{lane_id}")
lane_data = resp.json()
print(json.dumps(lane_data, indent=4))
data_source_id = lane_data["RawData"]

resp = post(
    f"http://localhost:5000/PixelClassificationWorkflow2/{workflow_id}/add_annotations",
    data=flatten(
        {
            "annotations": [
                {
                    "voxels": [{"x": 140, "y": 150}, {"x": 145, "y": 155}],
                    "color": {"r": 0, "g": 255, "b": 0},
                    "raw_data": data_source_id,
                },
                {
                    "voxels": [{"x": 238, "y": 101}, {"x": 229, "y": 139}],
                    "color": {"r": 0, "g": 255, "b": 0},
                    "raw_data": data_source_id,
                },
                {
                    "voxels": [{"x": 283, "y": 87}, {"x": 288, "y": 92}],
                    "color": {"r": 255, "g": 0, "b": 0},
                    "raw_data": data_source_id,
                },
                {
                    "voxels": [{"x": 274, "y": 168}, {"x": 256, "y": 191}],
                    "color": {"r": 255, "g": 0, "b": 0},
                    "raw_data": data_source_id,
                },
            ]
        }
    ),
)
annot_ids = resp.json()
print(f"Annotation ids: {annot_ids}")

resp = post(
    f"http://localhost:5000/PixelClassificationWorkflow2/{workflow_id}/add_ilp_feature_extractors",
    data=flatten(
        [
            {"name": "GaussianSmoothing", "scale": 0.3, "axis_2d": "z", "num_input_channels": 3},
            {"name": "GaussianSmoothing", "scale": 1.0, "axis_2d": "z", "num_input_channels": 3},
            {"name": "GaussianSmoothing", "scale": 1.6, "axis_2d": "z", "num_input_channels": 3},
            {"name": "HessianOfGaussianEigenvalues", "scale": 0.7, "axis_2d": "z", "num_input_channels": 3},
        ]
    ),
)
feature_ids = resp.json()
print(f"feature ids:: {feature_ids}")


resp = get(f"http://localhost:5000/PixelClassificationWorkflow2/{workflow_id}/get_classifier")
classifier_id = resp.json()
print(f"Classifier id: {classifier_id}")

resp = get(f"http://localhost:5000/predictions/{classifier_id}/neuroglancer_shader")
print(f"SHADER:\n{resp.text}")

predictions_path = f"predictions/{classifier_id}/{data_source_id}"
info = get(f"http://localhost:5000/{predictions_path}/info").json()
print(f"INFO:\n{json.dumps(info, indent=4)}")


binary = get(f"http://localhost:5000/{predictions_path}/data/0-256_0-256_0-1").content
data = numpy.frombuffer(binary, dtype=numpy.uint8).reshape(2, 256, 256)
a = Array5D(data, axiskeys="cyx")
a.show_channels()


ilp_contents = get(f"http://localhost:5000/PixelClassificationWorkflow2/{workflow_id}/ilp_project").content
with open("/tmp/generated_project.ilp", "wb") as f:
    f.write(ilp_contents)

workflow_data = get(f"http://localhost:5000/PixelClassificationWorkflow2/{workflow_id}").json()
print(json.dumps(workflow_data, indent=4))

resp = post(
    f"http://localhost:5000/PixelClassificationWorkflow2/{workflow_id}/upload_to_cloud_ilastik",
    data=flatten(
        {"cloud_ilastik_token": os.environ["CLOUD_ILASTIK_TOKEN"], "project_name": f"MyTestProject_{time.time()}"}
    ),
)
upload_data = resp.json()
print(json.dumps(upload_data, indent=4))
