import pytest
from lazyflow.graph import Graph
from lazyflow.operators.ioOperators import OpTiffReader
from lazyflow.utility.resolution import UnitAxisTags
import tifffile
import pathlib


@pytest.mark.parametrize(
    "image_path,checktags",
    [
        (f"/pix_res/2d.tif", {"x": (2, "cm"), "y": (7, "nm")}),
        (f"/pix_res/3d.tif", {"x": (11, "cm"), "y": (6, "mm"), "z": (2, "pm")}),
        (f"/pix_res/2d_t.tif", {"x": (50, "μm"), "y": (3, "pm"), "t": (3, "min")}),
        (f"/pix_res/3d_t.tif", {"x": (3, "mm"), "y": (5, ""), "z": (7, ""), "t": (3, "")}),
        (f"/pix_res/3d_c.tif", {"x": (2, "μm"), "y": (11, "nm"), "z": (13, "cm"), "c": ()}),
        (f"/pix_res/5d.tif", {"x": (17, "cm"), "y": (13, "pm"), "z": (8, "nm"), "c": (), "t": (3, "hr")}),
    ],
)
def test_read(image_path, checktags, inputdata_dir):  # checks
    actual_path = inputdata_dir + image_path
    op = OpTiffReader(graph=Graph())
    op.Filepath.setValue(actual_path)
    assert op.Output.ready()
    assert len(op.Output.meta.axistags) == len(checktags)
    for axis in checktags.keys():
        if axis == "c":
            continue
        (resolution, unit) = checktags[axis]
        tag = op.Output.meta.axistags[axis]
        assert tag.resolution == resolution
        assert op.Output.meta.axistags[axis].unit == unit
