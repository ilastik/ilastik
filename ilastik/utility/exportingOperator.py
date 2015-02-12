from ilastik.utility.exportFile import ProgressPrinter
from lazyflow.request import Request
from ilastik.widgets.exportObjectInfoDialog import ExportObjectInfoDialog
from functools import partial
from ilastik.widgets.progressDialog import ProgressDialog


class ExportingOperator(object):
    def __init__(self, *args, **kwargs):
        pass

    def export_object_data(self, settings, selected_features, gui=None):

        self.save_export_progress_dialog(None)
        if gui is None or "dialog" not in gui:
            progress_display = ProgressPrinter("Export Progress", xrange(100, -1, -5), 2)
        else:
            progress_display = gui["dialog"]
            self.save_export_progress_dialog(progress_display)

        export = partial(self.do_export, settings, selected_features, progress_display)
        request = Request(export)
        request.notify_failed(gui["fail"] if gui is not None and "fail" in gui else self.export_failed)
        request.notify_finished(gui["ok"] if gui is not None and "ok" in gui else self.export_finished)
        request.notify_cancelled(gui["cancel"] if gui is not None and "cancel" in gui else self.export_cancelled)
        request.submit()

        if gui is not None and "dialog" in gui:
            progress_display.cancel.connect(request.cancel)

    @staticmethod
    def export_failed(exception, traceback):
        print "Export Failed:", exception, traceback

    @staticmethod
    def export_finished(status):
        print "Export Finished", status

    @staticmethod
    def export_cancelled():
        print "Export Cancelled"

    def do_export(self, settings, selected_features, progress_slot):
        raise NotImplementedError

    def save_export_progress_dialog(self, dialog):
        raise NotImplementedError


class ExportingGui(object):
    def __init__(self, *args, **kwargs):
        pass

    def show_export_dialog(self):
        dimensions = self.get_raw_shape()
        feature_names = self.get_feature_names()

        dialog = ExportObjectInfoDialog(dimensions, feature_names)
        if not dialog.exec_():
            return

        settings = dialog.settings()
        selected_features = dialog.checked_features()

        progress = ProgressDialog(["Feature Data", "Labeling Rois", "Raw Image", "Exporting"])
        progress.set_busy(True)
        progress.show()
        gui = {
            "dialog": progress,
            "ok": partial(progress.safe_popup, "information", "Information", "Export successful!"),
            "cancel": partial(progress.safe_popup, "information", "Information", "Export cancelled!"),
            "fail": partial(progress.safe_popup, "critical", "Critical", "Export failed!")
        }
        self.topLevelOperatorView.export_object_data(settings, selected_features, gui)

    def get_raw_shape(self):
        raise NotImplementedError

    def get_feature_names(self):
        raise NotImplementedError