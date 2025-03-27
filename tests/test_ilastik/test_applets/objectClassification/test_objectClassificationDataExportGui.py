import os
from unittest.mock import MagicMock, patch
from ilastik.applets.objectClassification.objectClassificationDataExportGui import ObjectClassificationDataExportGui


def test_configure_table_export_sets_filename():
    # Mock objects
    mock_operator = MagicMock()
    mock_operator.InputImageName.value = "/path/to/image.tif"

    mock_exporter = MagicMock()
    mock_applet = MagicMock()

    # Create GUI instance
    gui = ObjectClassificationDataExportGui(
        parentApplet=mock_applet,
        topLevelOperator=mock_operator,
        table_exporter=mock_exporter
    )

    # Patch the QFileDialog.getSaveFileName to simulate user selection
    with patch("ilastik.applets.objectClassification.objectClassificationDataExportGui.QFileDialog.getSaveFileName") as mock_dialog:
        mock_dialog.return_value = ("/path/to/image_features.csv", "CSV Files (*.csv)")

        # Run the method
        gui.configure_table_export()

        # Check that the exporter's output filename was set correctly
        mock_exporter.OutputFilenameFormat.setValue.assert_called_once_with("/path/to/image_features.csv")


def test_configure_table_export_handles_missing_input_image_name():
    # Mock operator that raises exception when accessing InputImageName
    mock_operator = MagicMock()
    type(mock_operator.InputImageName).value = property(lambda self: (_ for _ in ()).throw(Exception("missing")))

    mock_exporter = MagicMock()
    mock_applet = MagicMock()

    gui = ObjectClassificationDataExportGui(
        parentApplet=mock_applet,
        topLevelOperator=mock_operator,
        table_exporter=mock_exporter
    )

    # Patch QFileDialog to simulate user selecting file even when default is blank
    with patch("ilastik.applets.objectClassification.objectClassificationDataExportGui.QFileDialog.getSaveFileName") as mock_dialog:
        mock_dialog.return_value = ("/user/selected/path.csv", "CSV Files (*.csv)")

        gui.configure_table_export()

        # Should still set the value even though default_filename was ""
        mock_exporter.OutputFilenameFormat.setValue.assert_called_once_with("/user/selected/path.csv")

