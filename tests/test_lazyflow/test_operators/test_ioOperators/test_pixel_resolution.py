import pytest
from lazyflow.graph import Graph
from lazyflow.operators.ioOperators import OpTiffReader
from lazyflow.utility.pixelSize import UnitAxisTags
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


@pytest.mark.parametrize(
    "image_path,checktags, hyperstack",
    [
        (f"2d.tif", {"x": (2, "cm"), "y": (7, "nm")}, False),
        (f"3d.tif", {"x": (11, "cm"), "y": (6, "mm"), "z": (2, "pm")}, True),
        (f"2d_t.tif", {"x": (50, "μm"), "y": (3, "pm"), "t": (3, "sec")}, True),
        (f"3d_t.tif", {"x": (3, "mm"), "y": (5, "mm"), "z": (7, "mm"), "t": (3, "sec")}, True),
        (f"3d_c.tif", {"x": (2, "μm"), "y": (11, "nm"), "z": (13, "cm"), "c": ()}, True),
        (f"5d.tif", {"x": (17, "cm"), "y": (13, "pm"), "z": (8, "mm"), "c": (), "t": (3, "sec")}, True),
    ],
)
def test_write(image_path, checktags, hyperstack, inputdata_dir):
    in_path = inputdata_dir + f"/pix_res/" + image_path
    out_path = inputdata_dir + f"/pix_res/output/" + image_path
    if not hyperstack:
        with tifffile.TiffFile(in_path) as tif:
            metadata = tif.imagej_metadata
            olddata = tif.asarray()
            data = olddata.squeeze()
            axes = metadata.get("axes")
            if "c" in checktags.keys():
                axes = "CYX"
            x = (checktags["x"][1].encode("unicode_escape").decode("ascii"),)
            y = (checktags["y"][1].encode("unicode_escape").decode("ascii"),)
            imagej_metadata = {
                "spacing": 1.0,  # this is equal to the z-axis and gets handled differently in non-2d images
                "unit": x,
                "yunit": y,
                "axes": axes,
            }
            tifffile.imwrite(
                out_path,
                data,
                imagej=True,
                metadata=imagej_metadata,
                resolution=(1 / (checktags["x"][0]), 1 / (checktags["y"][0])),
            )
    else:
        with tifffile.TiffFile(in_path) as tif:
            images = tif.asarray()
            ij_meta = tif.imagej_metadata

            axes = ""
            sizeC = ij_meta.get("channels", 1)
            sizeZ = ij_meta.get("slices", 1)
            sizeT = ij_meta.get("frames", 1)
            if sizeT > 1:
                axes += "T"
            if sizeZ > 1:
                axes += "Z"
            if sizeC > 1:
                axes += "C"
            axes += "YX"

            meta_dict = {
                "axes": axes,
                "SignificantBits": 8,
            }

            size_trans = {"x": "PhysicalSizeX", "y": "PhysicalSizeY", "z": "PhysicalSizeZ", "t": "TimeIncrement"}
            unit_trans = {
                "x": "PhysicalSizeXUnit",
                "y": "PhysicalSizeYUnit",
                "z": "PhysicalSizeZUnit",
                "t": "TimeIncrementUnit",
            }
            for axis in axes:
                axis = axis.lower()
                if axis in size_trans:
                    meta_dict[size_trans[axis]] = None
                    meta_dict[unit_trans[axis]] = None

            for unit in checktags.keys():
                if unit == "c":
                    continue
                meta_dict[size_trans[unit]] = checktags[unit][0]
                if checktags[unit][1] is not None:
                    meta_dict[unit_trans[unit]] = checktags[unit][1].encode("unicode_escape").decode("ascii")
                else:
                    meta_dict[unit_trans[unit]] = None

        with tifffile.TiffWriter(out_path, byteorder="<", ome=True) as writer:
            writer.write(
                images,
                software="ilastik",
                metadata=meta_dict,
                shape=images.shape,
            )

    # read written file
    op = OpTiffReader(graph=Graph())
    op.Filepath.setValue(out_path)
    assert op.Output.ready()
    assert len(op.Output.meta.axistags) == len(checktags)
    for axis in op.Output.meta.getAxisKeys():
        if axis == "c":
            continue
        (resolution, unit) = checktags[axis]
        tag = op.Output.meta.axistags[axis]
        assert tag.resolution == resolution
        assert tag.unit == unit
