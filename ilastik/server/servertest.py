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


def get_data(endpoint: str, ref):
    return get(f"http://localhost:5000/{endpoint}/{ref['object_id']}").json()


resp = post("http://localhost:5000/PixelClassificationWorkflow2/", data={})
workflow_ref = resp.json()
print("~~~~~~~> Workflow ref: ", workflow_ref)

datasources = get("http://localhost:5000/DataSource/").json()
print("~~~~~~>>>> datasources:")
print(json.dumps(datasources, indent=4))
for ds_data in datasources:
    if ds_data["name"] == "cropped1.png":
        data_source_data = ds_data
        _data_source_id = ds_data["__self__"]["object_id"]
        break
print(f"cropped1 datasource id: {_data_source_id}")

precomputed_url = f"precomputed://http://localhost:5000/datasource/{_data_source_id}/data"
resp = post(
    f"http://localhost:5000/rpc/add_lane_for_url", data=flatten({"__self__": workflow_ref, "url": precomputed_url})
)
lane_ref = resp.json()
print(f"~~~~~~~>>> Lane ref:")
print(json.dumps(lane_ref, indent=4))


lane_data = get_data("data_lane", lane_ref)
print(f"~~~~~~~>>> Lane data:")
print(json.dumps(lane_data, indent=4))

gui_datasource_data = get_data("gui_data_source", lane_data["RawData"])
print(f"~~~~~~~>>> GuiDataSource data:")
print(json.dumps(gui_datasource_data, indent=4))

datasource_data = get_data("data_source", gui_datasource_data["datasource"])
print(f"~~~~~~~>>> DataSource data:")
print(json.dumps(datasource_data, indent=4))
datasource_ref = datasource_data["__self__"]

resp = post(
    f"http://localhost:5000/rpc/add_annotations",
    data=flatten(
        {
            "__self__": workflow_ref,
            "annotations": [
                {
                    "voxels": [{"x": 140, "y": 150}, {"x": 145, "y": 155}],
                    "color": {"r": 0, "g": 255, "b": 0},
                    "raw_data": datasource_ref,
                },
                {
                    "voxels": [{"x": 238, "y": 101}, {"x": 229, "y": 139}],
                    "color": {"r": 0, "g": 255, "b": 0},
                    "raw_data": datasource_ref,
                },
                {
                    "voxels": [{"x": 283, "y": 87}, {"x": 288, "y": 92}],
                    "color": {"r": 255, "g": 0, "b": 0},
                    "raw_data": datasource_ref,
                },
                {
                    "voxels": [{"x": 274, "y": 168}, {"x": 256, "y": 191}],
                    "color": {"r": 255, "g": 0, "b": 0},
                    "raw_data": datasource_ref,
                },
            ],
        }
    ),
)
annot_ids = resp.json()
print(f"Annotation ids:")
print(json.dumps(annot_ids, indent=4))

resp = post(
    f"http://localhost:5000/rpc/add_ilp_feature_extractors",
    data=flatten(
        {
            "__self__": workflow_ref,
            "extractor_specs": [
                {"name": "GaussianSmoothing", "scale": 0.3, "axis_2d": "z", "num_input_channels": 3},
                {"name": "GaussianSmoothing", "scale": 1.0, "axis_2d": "z", "num_input_channels": 3},
                {"name": "GaussianSmoothing", "scale": 1.6, "axis_2d": "z", "num_input_channels": 3},
                {"name": "HessianOfGaussianEigenvalues", "scale": 0.7, "axis_2d": "z", "num_input_channels": 3},
            ],
        }
    ),
)
feature_ids = resp.json()
print(f"feature ids:: ")
print(json.dumps(feature_ids, indent=4))


classifier_ref = post(f"http://localhost:5000/rpc/get_classifier", data=flatten({"__self__": workflow_ref})).json()
print(f"Classifier ref:")
print(json.dumps(classifier_ref, indent=4))

resp = get(f"http://localhost:5000/predictions/{classifier_ref['object_id']}/neuroglancer_shader")
print(f"SHADER:\n{resp.text}")

predictions_path = f"predictions/{classifier_ref['object_id']}/{_data_source_id}"
info = get(f"http://localhost:5000/{predictions_path}/info").json()
print(f"INFO:\n{json.dumps(info, indent=4)}")


binary = get(f"http://localhost:5000/{predictions_path}/data/0-256_0-256_0-1").content
data = numpy.frombuffer(binary, dtype=numpy.uint8).reshape(2, 256, 256)
a = Array5D(data, axiskeys="cyx")
a.show_channels()

ilp_contents = post(f"http://localhost:5000/rpc/ilp_project", data=flatten({"__self__": workflow_ref})).content
ilp_filename = "/tmp/generated_project.ilp"
with open(ilp_filename, "wb") as f:
    f.write(ilp_contents)
print(f"**********WROTE CONTENTS OF .ilp PROJECT TO {ilp_filename}")

# workflow_data = get(f"http://localhost:5000/PixelClassificationWorkflow2/{workflow_ref}").json()
# print(json.dumps(workflow_data, indent=4))

resp = post(
    f"http://localhost:5000/rpc/upload_to_cloud_ilastik",
    data=flatten(
        {
            "__self__": workflow_ref,
            "cloud_ilastik_token": os.environ["CLOUD_ILASTIK_TOKEN"],
            "project_name": f"MyTestProject_{time.time()}",
        }
    ),
)
upload_data = resp.json()
print(json.dumps(upload_data, indent=4))
