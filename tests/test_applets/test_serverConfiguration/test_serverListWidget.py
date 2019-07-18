import pytest

from PyQt5.Qt import Qt

from ilastik.applets.serverConfiguration.serverListWidget import ServerListModel, ServerListWidget


class TestServerListWidget:
    @pytest.fixture
    def model(self):
        return ServerListModel(data=[
            {"name": "MySrv1"},
            {"name": "MySrv2", "type": "local"},
        ])

    @pytest.fixture
    def widget(self, qtbot, model):
        w = ServerListWidget()
        w.setModel(model)
        w.show()
        qtbot.addWidget(w)
        return w

    def test_add_new(self, qtbot, model, widget):
        assert 2 == model.rowCount()

        qtbot.mouseClick(widget.addBtn, Qt.LeftButton)

        assert 3 == model.rowCount()

    def test_remove(self, qtbot, model, widget):
        assert 2 == model.rowCount()

        qtbot.mouseClick(widget.rmBtn, Qt.LeftButton)

        assert 1 == model.rowCount()
