import pytest
from lazyflow.graph import Graph
from lazyflow.operators.ioOperators import OpTiffReader


@pytest.mark.parametrize(
    "image_path,checktags",
    [
        (f"/pix_res/2d.tiff", {"x": (2, "cm"), "y": (7, "nm")}),
        (f"/pix_res/3d.tiff", {"x": (11, "cm"), "y": (6, "mm"), "z": (2, "pm")}),
        (f"/pix_res/2d_t.tif", {"x": (50, "μm"), "y": (3, "pm"), "t": (3, "sec")}),
        (f"/pix_res/3d_t.tif", {"x": (3, "mm"), "y": (5, "mm"), "z": (7, "mm"), "t": (3, "sec")}),
        (f"/pix_res/3d_c.tif", {"x": (2, "μm"), "y": (11, "nm"), "z": (13, "cm"), "c": ()}),
        (f"/pix_res/5d.tif", {"x": (17, "cm"), "y": (13, "pm"), "z": (8, "mm"), "c": (), "t": (3, "sec")}),
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
        assert op.Output.meta.axistags.getUnitTag(axis) == unit


@pytest.mark.parametrize(
    "image_path,checktags",
    [
        (f"/pix_res/2d_t.tiff", "xyt"),
        (f"/pix_res/3d_c.tiff", "xyzc"),
    ],
)
def test_read_problematic_units(
    image_path, checktags, inputdata_dir
):  # this currently checks and handles images with improper units (including mu symbol atm)
    actual_path = inputdata_dir + image_path
    op = OpTiffReader(graph=Graph())
    op.Filepath.setValue(actual_path)
    assert op.Output.ready()
    assert len(op.Output.meta.axistags) == len(checktags)
    for axis in checktags:
        assert op.Output.meta.axistags[axis]
        tag = op.Output.meta.axistags[axis]
        assert tag.resolution == 0
        assert op.Output.meta.axistags.getUnitTag(axis) == None


# keeping this here for when mu symbol is handled properly
"""
@pytest.mark.parametrize(
    "image_path,checktags",
    [
        (f"/pix_res/2d.tiff", {'x': (2, "cm"), 'y': (7, "nm")}),
        (f"/pix_res/3d.tiff", {'x': (11, "cm"), 'y': (6, "mm"), 'z': (2, "pm")}),
        (f"/pix_res/2d_t.tif", {'x': (50, "μm"), 'y': (3, "pm"), 't': (3, "sec")}),
        (f"/pix_res/3d_t.tif", {'x': (3, "mm"), 'y': (5,"mm"), 'z': (7,"mm"), 't': (3, "sec")}),
        (f"/pix_res/3d_c.tif", {'x': (2, "μm"), 'y': (11,"nm"), 'z': (13,"cm"), 'c': ()}),
        (f"/pix_res/5d.tif", {'x': (17,"cm"), 'y': (13,"pm"), 'z': (8,"mm"), 'c': (), 't': (3, "sec")})
    ],
)
"""
