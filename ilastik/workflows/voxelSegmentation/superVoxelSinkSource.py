from volumina.api import LazyflowSinkSource


class SuperVoxelSinkSource(LazyflowSinkSource):
    def put(self, slicing, array):
        return super().put(slicing, array)
