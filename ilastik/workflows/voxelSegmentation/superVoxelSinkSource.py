from volumina.api import LazyflowSinkSource


class SuperVoxelSinkSource(LazyflowSinkSource):
    def put(self, slicing, array):
        print("svss")
        return super().put(slicing, array)
