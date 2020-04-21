"""HBP-specific utilities."""

import functools
import io
import types
from dataclasses import dataclass
from typing import Mapping, Optional, Type, Union

import h5py
import numpy
import requests

from ilastik.applets.dataSelection.opDataSelection import OpDataSelectionGroup
from ilastik.applets.featureSelection.opFeatureSelection import OpFeatureSelection
from ilastik.config import cfg
from ilastik.workflow import Workflow
from ilastik.workflows import PixelClassificationWorkflow
from ilastik.workflows.objectClassification.objectClassificationWorkflow import ObjectClassificationWorkflow


CATEGORIES: Mapping[Type[Workflow], str] = types.MappingProxyType(
    {PixelClassificationWorkflow: "pixel_classification", ObjectClassificationWorkflow: "object_classification"}
)

ORDERS: Mapping[str, int] = types.MappingProxyType(
    {
        "GaussianSmoothing": 0,
        "LaplacianOfGaussian": 2,
        "GaussianGradientMagnitude": 1,
        "DifferenceOfGaussians": 0,
        "StructureTensorEigenvalues": 1,
        "HessianOfGaussianEigenvalues": 2,
    }
)


def category(workflow: Workflow) -> str:
    """Workflow category name, or empty string if HBP server does not support the workflow."""
    return next((cat for cls, cat in CATEGORIES.items() if isinstance(workflow, cls)), "")


def halo(*, scale: float, order: int) -> int:
    """Compute halo size from scale and filter order."""
    return int(3 * scale + 0.5 * order + 0.5)


@dataclass
class Payload:
    """Data for uploading a project to HBP server."""

    token: str
    project: bytes
    filename: str
    num_channels: int
    min_block_size: int
    compute_in_2d: bool
    workflow: str


def send_payload(payload: Payload, *, timeout: int = 10) -> str:
    """Upload a file, create a project resource and return a human-viewable webpage URL."""
    token_headers = {"Authorization": f"Token {payload.token}"}

    upload_resp = requests.post(
        cfg["hbp"]["upload_file_url"],
        data=payload.project,
        headers={**token_headers, "Content-Disposition": f'attachment; filename="{payload.filename}"'},
        timeout=timeout,
    )
    upload_resp.raise_for_status()

    project_resp = requests.post(
        cfg["hbp"]["create_project_url"],
        json={
            "file": upload_resp.json()["url"],
            "workflow": payload.workflow,
            "num_channels": payload.num_channels,
            "min_block_size_z": 0 if payload.compute_in_2d else payload.min_block_size,
            "min_block_size_y": payload.min_block_size,
            "min_block_size_x": payload.min_block_size,
        },
        headers=token_headers,
        timeout=timeout,
    )
    project_resp.raise_for_status()

    return project_resp.json()["html_url"]


def partial_copy(
    name: str, obj: Union[h5py.Group, h5py.Dataset], *, dest: h5py.Group, skip_prefix: Optional[str] = None
) -> None:
    """Deep copy obj to dest, but skip contents of datasets whose names start with the prefix.

    If `skip_prefix` is ``None``, include all datasets' contents.
    If `skip_prefix` is an empty string, skip all datasets' contents.

    Intended to be used as a curried callback for :meth:`h5py.Group.visititems`.
    """
    if isinstance(obj, h5py.Group):
        group = dest.create_group(name)
        group.attrs.update(obj.attrs)
    elif isinstance(obj, h5py.Dataset) and skip_prefix is not None and name.startswith(skip_prefix):
        dataset = dest.create_dataset_like(name, obj)
        dataset.attrs.update(obj.attrs)
    else:
        dest.copy(obj, name)


def serialize_project_file(project_file: h5py.File, *, include_local_data: bool = False) -> bytes:
    """Convert project file into byte representation."""
    skip_prefix = "Input Data/local_data" if include_local_data else None
    with io.BytesIO() as buf:
        with h5py.File(buf) as dest:
            project_file.visititems(functools.partial(partial_copy, dest=dest, skip_prefix=skip_prefix))
        return buf.getvalue()


def num_channels(op: OpDataSelectionGroup) -> int:
    role_index = op.DatasetRoles.value.index("Raw Data")
    dataset_info = op.DatasetGroup[0][role_index].value
    try:
        return dataset_info.laneShape[dataset_info.axistags.channelIndex]
    except IndexError:
        return 1


def min_block_size(op: OpFeatureSelection) -> int:
    selected = numpy.argwhere(op.SelectionMatrix.value)
    if not selected.size:
        return 0
    return max(halo(scale=op.Scales.value[col], order=ORDERS[op.FeatureIds.value[row]]) for row, col in selected)


def compute_in_2d(op: OpFeatureSelection) -> bool:
    selected = numpy.argwhere(op.SelectionMatrix.value)
    return any(op.ComputeIn2d.value[col] for _row, col in selected)
