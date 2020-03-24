import requests
import json
import numpy
from ilastik.utility import flatten, unflatten, listify
from ndstructs import Array5D


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
    "http://localhost:5000/sequence_data_source/",
    data={"path": "/home/tomaz/ilastikTests/SampleData/c_cells/cropped/cropped1.png"},
)
data_source_id = resp.json()

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
    f"http://localhost:5000/PixelClassificationWorkflow2/{workflow_id}/add_feature_extractors",
    data=flatten(
        {
            "extractors": [
                {"__class__": "GaussianSmoothing", "sigma": 0.3, "axis_2d": "z", "num_input_channels": 3},
                {"__class__": "HessianOfGaussianEigenvalues", "scale": 0.7, "axis_2d": "z", "num_input_channels": 3},
            ]
        }
    ),
)
feature_ids = resp.json()
print(f"feature ids:: {feature_ids}")

resp = get(f"http://localhost:5000/PixelClassificationWorkflow2/{workflow_id}/get_classifier")
classifier_id = resp.json()
print(f"Classifier id: {classifier_id}")

predictions_path = f"predictions/{classifier_id}/{data_source_id}"
info = get(f"http://localhost:5000/{predictions_path}/info").json()
print(f"INFO:\n{json.dumps(info, indent=4)}")


binary = get(f"http://localhost:5000/{predictions_path}/data/0-256_0-256_0-1").content
data = numpy.frombuffer(binary, dtype=numpy.uint8).reshape(2, 256, 256)
a = Array5D(data, axiskeys="cyx")
a.show_channels()


ilp_contents = get(f"http://localhost:5000/PixelClassificationWorkflow2/{workflow_id}/generate_ilp").content
with open("/tmp/generated_project.ilp", "wb") as f:
    f.write(ilp_contents)

exit(0)
################//////////////////
resp = post(
    "http://localhost:5000/data_source/",
    data={"path": "/home/tomaz/SampleData/n5tests/317_8_CamKII_tTA_lacZ_Xgal_s123_1.4.n5/data"},
)


resp = post(
    "http://localhost:5000/sequence_data_source/",
    data={"path": "/home/tomaz/ilastikTests/SampleData/c_cells/cropped/cropped1.png"},
)
data_source_id = resp.json()
print(f"data_source_id: {data_source_id}")
assert data_source_id.startswith("pointer@")


datasource_piece_raw = get(f"http://localhost:5000/datasource/{data_source_id}/data/0-100_0-100_0-1").content
datasource_piece_np = numpy.frombuffer(datasource_piece_raw, dtype=numpy.uint8).reshape(3, 100, 100)
Array5D(datasource_piece_np, axiskeys="cyx").show_images()


resp = post(
    "http://localhost:5000/annotation/",
    data={
        "voxels.0.x": 140,
        "voxels.0.y": 150,
        "voxels.1.x": 145,
        "voxels.1.y": 155,
        "color.r": 0,
        "color.g": 255,
        "color.b": 0,
        "raw_data": data_source_id,
    },
)
annot0_id = resp.json()

resp = post(
    "http://localhost:5000/annotation/",
    data={
        "voxels.0.x": 238,
        "voxels.0.y": 101,
        "voxels.1.x": 229,
        "voxels.1.y": 139,
        "color.r": 0,
        "color.g": 255,
        "color.b": 0,
        "raw_data": data_source_id,
    },
)
annot1_id = resp.json()

resp = post(
    "http://localhost:5000/annotation/",
    data={
        "voxels.0.x": 283,
        "voxels.0.y": 87,
        "voxels.1.x": 288,
        "voxels.1.y": 92,
        "color.r": 255,
        "color.g": 0,
        "color.b": 0,
        "raw_data": data_source_id,
    },
)
annot2_id = resp.json()

resp = post(
    "http://localhost:5000/annotation/",
    data={
        "voxels.0.x": 274,
        "voxels.0.y": 168,
        "voxels.1.x": 256,
        "voxels.1.y": 191,
        "color.r": 255,
        "color.g": 0,
        "color.b": 0,
        "raw_data": data_source_id,
    },
)
annot3_id = resp.json()


resp = post("http://localhost:5000/gaussian_smoothing/", data={"sigma": 0.3, "axis_2d": "z", "num_input_channels": 3})
gauss_id = resp.json()
print(f"gauss_id: {gauss_id}")
assert gauss_id.startswith("pointer@")


resp = post(
    "http://localhost:5000/hessian_of_gaussian_eigenvalues/",
    data={"scale": 0.3, "axis_2d": "z", "num_input_channels": 3},
)
hess_id = resp.json()
print(f"hess_id: {hess_id}")
assert hess_id.startswith("pointer@")

resp = get("http://localhost:5000/feature_extractor/")
print("Feature extractors:")
print(json.dumps(resp.json(), indent=4))

resp = get(f"http://localhost:5000/feature_extractor/{hess_id}").json()
print("Retrieveing hessian filter:\n", json.dumps(resp, indent=4))


resp = post(
    "http://localhost:5000/ilp_vigra_pixel_classifier/",
    data={
        "strict": "true",
        "feature_extractors.0": gauss_id,
        "feature_extractors.1": hess_id,
        "annotations.0": annot0_id,
        "annotations.1": annot1_id,
        "annotations.2": annot2_id,
        "annotations.3": annot3_id,
    },
)
classifier_id = resp.json()
print(f"classifier_id: {classifier_id}")
assert classifier_id.startswith("pointer@")


resp = get(
    "http://localhost:5000/predict/",
    params={"pixel_classifier_id": classifier_id, "data_source_id": data_source_id, "x": "100_200", "y": "100_200"},
)


info = get(f"http://localhost:5000/predictions/{classifier_id}/{data_source_id}/info").json()
print(json.dumps(info, indent=4))


predictions_path = f"predictions/{classifier_id}/{data_source_id}"
binary = get(f"http://localhost:5000/{predictions_path}/data/0-256_0-256_0-1").content
data = numpy.frombuffer(binary, dtype=numpy.uint8).reshape(2, 256, 256)
a = Array5D(data, axiskeys="cyx")
a.show_channels()

print("Use this URL in neuroglancer::::")
print("\nPredictions:")
print(f"precomputed://http://localhost:5000/{predictions_path}")

print("\nRaw:")
print(f"precomputed://http://localhost:5000/datasource/{data_source_id}")


print("\n\nRgb squares url:")
resp = post(
    "http://localhost:5000/data_source/",
    data={"path": "/home/tomaz/ilastikTests/SampleData/rgbtest/rgb_squares_rgb_no-alpha.png"},
)
rgb_squares_data_source_id = resp.json()
print(f"precomputed://http://localhost:5000/datasource/{rgb_squares_data_source_id}")
binary = get(f"http://localhost:5000/datasource/{rgb_squares_data_source_id}/data/0-10_0-10_0-1").content
data = numpy.frombuffer(binary, dtype=numpy.uint8).reshape(3, 10, 10)
a = Array5D(data, axiskeys="cyx")
a.show_channels()
