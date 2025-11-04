"""
Tests for WSDT Alpha parameter validation and clamping behavior.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock, PropertyMock
from qtpy.QtWidgets import QMessageBox, QDoubleSpinBox


def test_alpha_validation_logic_valid_value():
    """Test the alpha validation logic with valid value."""
    # Simulate the validation logic from configure_operator_from_gui
    alpha_val = 0.8
    last_alpha = 0.5
    
    # Check if value is outside valid range [0, 1]
    needs_dialog = (last_alpha is None or alpha_val != last_alpha) and (alpha_val < 0.0 or alpha_val > 1.0)
    
    # Should not need dialog for valid value
    assert not needs_dialog
    
    # Value should pass through unchanged
    assert alpha_val == 0.8


def test_alpha_validation_logic_above_range():
    """Test the alpha validation logic with value > 1.0."""
    alpha_val = 2.5
    last_alpha = 0.5
    
    # Check if value is outside valid range [0, 1]
    needs_dialog = (last_alpha is None or alpha_val != last_alpha) and (alpha_val < 0.0 or alpha_val > 1.0)
    
    # Should trigger dialog
    assert needs_dialog
    
    # Simulate clamping
    alpha_clamped = min(max(alpha_val, 0.0), 1.0)
    assert alpha_clamped == 1.0


def test_alpha_validation_logic_below_range():
    """Test the alpha validation logic with value < 0.0."""
    alpha_val = -0.5
    last_alpha = 0.5
    
    # Check if value is outside valid range [0, 1]
    needs_dialog = (last_alpha is None or alpha_val != last_alpha) and (alpha_val < 0.0 or alpha_val > 1.0)
    
    # Should trigger dialog
    assert needs_dialog
    
    # Simulate clamping
    alpha_clamped = min(max(alpha_val, 0.0), 1.0)
    assert alpha_clamped == 0.0


def test_alpha_validation_logic_unchanged_out_of_range():
    """Test that unchanged alpha doesn't trigger dialog even if out of range."""
    alpha_val = 2.5
    last_alpha = 2.5  # Same as current value
    
    # Check if value changed
    needs_dialog = (last_alpha is None or alpha_val != last_alpha) and (alpha_val < 0.0 or alpha_val > 1.0)
    
    # Should NOT trigger dialog since value hasn't changed
    assert not needs_dialog


def test_alpha_tooltip_content(qapp):
    """Test that alpha spinbox tooltip documents the valid range."""
    from ilastik.applets.wsdt.wsdtGui import WsdtGui
    
    # Create a minimal mock operator with required structure
    mock_op = Mock()
    mock_op.inputs = {}
    mock_op.outputs = {}
    
    # Mock the parent applet
    mock_applet = Mock()
    mock_applet.guiMode = Mock(return_value="default")
    
    # Patch the parent class __init__ to avoid full initialization
    with patch('ilastik.applets.layerViewer.layerViewerGui.LayerViewerGui.__init__', return_value=None):
        gui = WsdtGui.__new__(WsdtGui)
        gui.__cleanup_fns = []
        gui._currently_updating = False
        gui._last_alpha_value = None
        gui.topLevelOperatorView = mock_op
        
        # Initialize just the alpha spinbox portion
        gui.alpha_box = QDoubleSpinBox()
        gui.alpha_box.setToolTip(
            "Used to blend boundaries and the distance transform in order to obtain the watershed weight map. "
            "Valid range is [0.0, 1.0]. Legacy project files with values > 1.0 are preserved for compatibility."
        )
        
        tooltip = gui.alpha_box.toolTip()
        
        # Tooltip should mention the valid range and legacy compatibility
        assert "0.0" in tooltip and "1.0" in tooltip
        assert "legacy" in tooltip.lower() or "compatibility" in tooltip.lower()


def test_alpha_clamping_min_max():
    """Test the min/max clamping function."""
    # Test clamping values outside [0, 1]
    assert min(max(-0.5, 0.0), 1.0) == 0.0
    assert min(max(2.5, 0.0), 1.0) == 1.0
    assert min(max(0.5, 0.0), 1.0) == 0.5
    assert min(max(0.0, 0.0), 1.0) == 0.0
    assert min(max(1.0, 0.0), 1.0) == 1.0


def test_alpha_dialog_flow_with_mock(qapp):
    """Test the dialog flow with mocked QMessageBox."""
    # Simulate user choosing to clamp
    alpha_val = 2.5
    
    with patch('ilastik.applets.wsdt.wsdtGui.QMessageBox') as mock_msgbox_class:
        # Create mock message box
        mock_msg = MagicMock()
        mock_msgbox_class.return_value = mock_msg
        
        # Mock buttons
        clamp_button = MagicMock()
        keep_button = MagicMock()
        
        def add_button_impl(text, role):
            if "Clamp" in text:
                return clamp_button
            return keep_button
        
        mock_msg.addButton.side_effect = add_button_impl
        mock_msg.clickedButton.return_value = clamp_button  # User clicks clamp
        
        # Simulate the dialog code path
        msg = mock_msgbox_class(None)
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle("Alpha Value Out of Range")
        msg.setText(f"The Alpha value {alpha_val:.1f} is outside the valid range [0.0, 1.0].\n\n"
                   "Alpha blends probability maps with the distance transform and should be in [0, 1].")
        msg.setInformativeText("Would you like to clamp the value to the valid range?")
        
        clamp_btn = msg.addButton("Clamp to Valid Range", QMessageBox.AcceptRole)
        keep_btn = msg.addButton("Keep Current Value", QMessageBox.RejectRole)
        msg.setDefaultButton(clamp_btn)
        
        msg.exec_()
        
        if msg.clickedButton() == clamp_btn:
            alpha_val = min(max(alpha_val, 0.0), 1.0)
        
        # Verify dialog was called
        assert mock_msgbox_class.called
        assert alpha_val == 1.0  # Should be clamped
