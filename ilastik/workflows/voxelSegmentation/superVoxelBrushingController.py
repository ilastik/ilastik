from volumina.brushingcontroller import BrushingController


class SuperVoxelBrushingController(BrushingController):
    def _writeIntoSink(self, brushStrokeOffset, labels):
        print("WIS")
        print(brushStrokeOffset)
        print(labels)
