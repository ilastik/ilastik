###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2014, the ilastik developers
#                                <team@ilastik.org>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# In addition, as a special exception, the copyright holders of
# ilastik give you permission to combine ilastik with applets,
# workflows and plugins which are not covered under the GNU
# General Public License.
#
# See the LICENSE file for details. License information is also available
# on the ilastik web site at:
#           http://ilastik.org/license.html
###############################################################################
import os

import numpy as np
import h5py
import sys
import pytest
import shutil
import vigra

from lazyflow.utility.timer import timeLogged

import logging

logger = logging.getLogger(__name__)


class TestConservationTrackingHeadless(object):

    logger.info("looking for tests directory ...")
    input_data_path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "inputdata")
    if not os.path.exists(input_data_path):
        raise RuntimeError("Couldn't find ilastik/tests directory: {}".format(input_data_path))

    PROJECT_FILE = os.path.join(input_data_path, "smallVideoConservationTracking.ilp")
    RAW_DATA_FILE = os.path.join(input_data_path, "smallVideo.h5")
    BDV_XML_FILE = os.path.join(input_data_path, "smallVideoBdv.xml")
    BINARY_SEGMENTATION_FILE = os.path.join(input_data_path, "smallVideoSimpleSegmentation.h5")
    ILASTIK_MAIN_DEFAULT_ARGS = [
        f"--project={PROJECT_FILE}",
        "--headless",
        "--raw_data",
        os.path.join(RAW_DATA_FILE, "data"),
        "--segmentation_image",
        os.path.join(BINARY_SEGMENTATION_FILE, "exported_data"),
    ]

    EXPECTED_TRACKING_RESULT_FILE = os.path.join(input_data_path, "smallVideo-data_Tracking-Result.h5")
    EXPECTED_SHAPE = (7, 408, 408, 1)  # Expected shape for tracking results HDF5 files

    EXPECTED_CSV_FILE = os.path.join(input_data_path, "smallVideo-data_CSV-Table.csv")
    EXPECTED_NUM_ROWS = 23  # Number of lines expected in exported csv file
    EXPECTED_NUM_LINEAGES = 3
    EXPECTED_MERGER_NUM = 2  # Number of mergers expected in exported csv file
    EXPECTED_NUM_DIVISION_CHILDREN = (
        2  # Number of tracks that have their "parent" set, meaning they are children of a division
    )

    @classmethod
    def setup_class(cls):
        if (
            not os.path.isfile(cls.PROJECT_FILE)
            or not os.path.isfile(cls.RAW_DATA_FILE)
            or not os.path.isfile(cls.BINARY_SEGMENTATION_FILE)
        ):
            raise RuntimeError("Test input files not found.")

        logger.info("starting setup...")
        cls.original_cwd = os.getcwd()

        # Import here in setupClass to ensure loading only once.
        import ilastik.__main__

        cls.ilastik_startup = ilastik.__main__

    @classmethod
    def teardown_class(cls):
        removeFiles = [cls.EXPECTED_TRACKING_RESULT_FILE, cls.EXPECTED_CSV_FILE]

        # Clean up: Delete any test files we generated
        for f in removeFiles:
            try:
                os.remove(f)
            except:
                pass

    @timeLogged(logger)
    def testTrackingHeadless(self, tmp_path):
        output_path = tmp_path / "testTrackingHeadlessOutput.h5"

        args = self.ILASTIK_MAIN_DEFAULT_ARGS + [
            "--export_source=Tracking-Result",
            "--output_filename_format=" + str(output_path),
        ]

        sys.argv = ["ilastik.py"]  # Clear the existing commandline args so it looks like we're starting fresh.
        sys.argv += args

        # Start up the ilastik.py entry script as if we had launched it from the command line
        self.ilastik_startup.main()

        # Examine the HDF5 output for basic attributes
        with h5py.File(output_path, "r") as f:
            assert "exported_data" in f, "Dataset does not exist in tracking result file"
            shape = f["exported_data"].shape
            assert shape == self.EXPECTED_SHAPE, "Exported data has wrong shape: {}".format(shape)
            data = f["exported_data"][()]
            assert len(np.unique(data)) == self.EXPECTED_NUM_LINEAGES + 1  # background also shows up, hence + 1

    @timeLogged(logger)
    def testCSVExport(self):

        args = self.ILASTIK_MAIN_DEFAULT_ARGS + ["--export_source=Plugin", "--export_plugin=CSV-Table"]

        sys.argv = ["ilastik.py"]  # Clear the existing commandline args so it looks like we're starting fresh.
        sys.argv += args

        # Start up the ilastik.py entry script as if we had launched it from the command line
        self.ilastik_startup.main()

        # Load csv file
        data = np.genfromtxt(self.EXPECTED_CSV_FILE, dtype=float, delimiter=",", names=True)

        # Check for expected number of rows in csv table
        assert data.shape[0] == self.EXPECTED_NUM_ROWS, "Number of rows in csv file differs from expected"

        # Check that csv contains RegionRadii and RegionAxes (necessary for animal tracking)
        assert (
            "Radii_of_the_object_0" in data.dtype.names
        ), "RegionRadii not found in csv file (required for animal tracking)"
        assert (
            "Principal_components_of_the_object_0" in data.dtype.names
        ), "RegionAxes not found in csv file (required for animal tracking)"

        # Check for expected number of mergers
        mergerIds = set([])
        for row, mergerId in enumerate(data["mergerLabelId"]):
            if mergerId != 0:
                mergerIds.add((int(data["frame"][row]), int(mergerId)))
        merger_count = len(mergerIds)
        assert merger_count == self.EXPECTED_MERGER_NUM, "Number of mergers in csv file differs from expected"

        tracks_with_parent = 0
        for p in data["parentTrackId"]:
            if p != 0:
                tracks_with_parent += 1

        # Check for expected number of rows in divisions csv table (we only have one division in the video)
        assert (
            tracks_with_parent == self.EXPECTED_NUM_DIVISION_CHILDREN
        ), "Number of children divisions differs from expected"

    @timeLogged(logger)
    def testCTCExport(self):

        args = self.ILASTIK_MAIN_DEFAULT_ARGS + ["--export_source=Plugin", "--export_plugin=CellTrackingChallenge"]

        sys.argv = ["ilastik.py"]  # Clear the existing commandline args so it looks like we're starting fresh.
        sys.argv += args

        # Start up the ilastik.py entry script as if we had launched it from the command line
        self.ilastik_startup.main()

        # check res_track file exists
        resTrackFilename = os.path.join(self.input_data_path, "smallVideo-data_CellTrackingChallenge", "res_track.txt")
        assert os.path.exists(resTrackFilename), "res_track not found"
        a = np.genfromtxt(resTrackFilename, dtype=np.uint32, delimiter=" ")
        assert a.shape == (5, 4)
        # check that ids are starting at 1 and are consecutive
        assert np.all(np.sort(a[:, 0]) == np.arange(1, 6))
        # check that parent IDs are present in tracks or zero
        parents = np.unique(a[:, 3])
        for p in parents:
            assert p == 0 or p in a[:, 0], "Parent is invalid track ID"

        # check whether images exist
        for i in range(7):
            assert os.path.exists(
                os.path.join(self.input_data_path, "smallVideo-data_CellTrackingChallenge", f"mask00{i}.tif")
            ), f"Missing frame {i}"

        # check that the first frame contains consecutive trackIDs starting at 1, where 0 is background
        imagePath = os.path.join(self.input_data_path, "smallVideo-data_CellTrackingChallenge", "mask000.tif")
        image = vigra.impex.readImage(imagePath, dtype=np.uint32)
        assert set(np.unique(image)) == set(
            range(image.max() + 1)
        ), "First frame does not contain consecutive IDs starting at 1!"

        # cleanup
        shutil.rmtree(os.path.join(self.input_data_path, "smallVideo-data_CellTrackingChallenge"))

    @timeLogged(logger)
    def testHDF5Export(self):

        args = self.ILASTIK_MAIN_DEFAULT_ARGS + ["--export_source=Plugin", "--export_plugin=H5-Event-Sequence"]

        sys.argv = ["ilastik.py"]  # Clear the existing commandline args so it looks like we're starting fresh.
        sys.argv += args

        # Start up the ilastik.py entry script as if we had launched it from the command line
        self.ilastik_startup.main()

        # check output files exist
        for i in range(7):
            assert os.path.exists(
                os.path.join(self.input_data_path, "smallVideo-data_H5-Event-Sequence", f"0000{i}.h5")
            ), f"Missing frame {i}"
        shutil.rmtree(os.path.join(self.input_data_path, "smallVideo-data_H5-Event-Sequence"))

    @timeLogged(logger)
    def testMamutExport(self):
        try:
            from mamutexport.mamutxmlbuilder import MamutXmlBuilder
        except:
            pytest.xfail("Mamutexport module not present. Skipping test")

        args = self.ILASTIK_MAIN_DEFAULT_ARGS + [
            "--export_source=Plugin",
            "--export_plugin=Fiji-MaMuT",
            "--big_data_viewer_xml_file=" + self.BDV_XML_FILE,
        ]

        sys.argv = ["ilastik.py"]  # Clear the existing commandline args so it looks like we're starting fresh.
        sys.argv += args

        # Start up the ilastik.py entry script as if we had launched it from the command line
        self.ilastik_startup.main()

        # check output files exist
        files = [os.path.join(self.input_data_path, "smallVideo-data_Fiji-MaMuT_mamut.xml")]

        for f in files:
            assert os.path.exists(f)
            os.remove(f)

    @timeLogged(logger)
    def testJsonExport(self):
        try:
            from mamutexport.mamutxmlbuilder import MamutXmlBuilder
        except:
            pytest.xfail("Mamutexport module not present. Skipping test")

        args = self.ILASTIK_MAIN_DEFAULT_ARGS + ["--export_source=Plugin", "--export_plugin=JSON"]

        sys.argv = ["ilastik.py"]  # Clear the existing commandline args so it looks like we're starting fresh.
        sys.argv += args

        # Start up the ilastik.py entry script as if we had launched it from the command line
        self.ilastik_startup.main()

        # check output files exist
        files = [
            os.path.join(self.input_data_path, "smallVideo-data_JSON_graph.json"),
            os.path.join(self.input_data_path, "smallVideo-data_JSON_result.json"),
        ]

        for f in files:
            assert os.path.exists(f)
            os.remove(f)
