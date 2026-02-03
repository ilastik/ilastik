import numpy as np
import pytest

import ilastik.applets.layerViewer.layerViewerGui as lvmod


class DummyMeta:
    def __init__(self, dtype, normalizeDisplay=False, drange=None):
        self.dtype = dtype
        self.normalizeDisplay = normalizeDisplay
        self.drange = drange


class DummySlot:
    def __init__(self, dtype):
        self.meta = DummyMeta(dtype=dtype, normalizeDisplay=False, drange=None)
        self.name = "dummy"


def test_float_mask_uses_grayscale(monkeypatch):
    created = {}

    # Monkeypatch createDataSource to return a sentinel
    monkeypatch.setattr(lvmod, "createDataSource", lambda slot: "SRC")

    # Dummy GrayscaleLayer that records its args
    class DummyGray:
        def __init__(self, src, window_leveling=True, priority=None):
            created['type'] = 'gray'
            created['src'] = src
            created['window_leveling'] = window_leveling
            created['priority'] = priority

        def set_normalize(self, channel, val):
            created['normalize'] = (channel, val)

    # Dummy ColortableLayer that records if it was created
    class DummyCT:
        def __init__(self, src, colortable, priority=None):
            created['type'] = 'colortable'
            created['src'] = src
            created['colortable_len'] = len(colortable)
            created['priority'] = priority

    monkeypatch.setattr(lvmod, 'GrayscaleLayer', DummyGray)
    monkeypatch.setattr(lvmod, 'ColortableLayer', DummyCT)

    slot = DummySlot(np.dtype('float32'))

    layer = lvmod.LayerViewerGui._create_binary_mask_layer_from_slot(slot)

    assert created.get('type') == 'gray', f"expected grayscale layer for float dtype, got {created}"
    assert created.get('src') == 'SRC'
    # normalization default for floats should be set to (0.0, 1.0) unless meta specifies otherwise
    assert created.get('normalize') == (0, (0.0, 1.0))


def test_integer_mask_uses_colortable(monkeypatch):
    created = {}
    monkeypatch.setattr(lvmod, "createDataSource", lambda slot: "SRC")

    class DummyGray:
        def __init__(self, src, window_leveling=True, priority=None):
            created['type'] = 'gray'

    class DummyCT:
        def __init__(self, src, colortable, priority=None):
            created['type'] = 'colortable'
            created['src'] = src
            created['colortable_len'] = len(colortable)

    monkeypatch.setattr(lvmod, 'GrayscaleLayer', DummyGray)
    monkeypatch.setattr(lvmod, 'ColortableLayer', DummyCT)

    slot = DummySlot(np.dtype('uint8'))
    layer = lvmod.LayerViewerGui._create_binary_mask_layer_from_slot(slot)

    assert created.get('type') == 'colortable', f"expected colortable layer for integer dtype, got {created}"
    assert created.get('src') == 'SRC'
    assert created.get('colortable_len') == 256
