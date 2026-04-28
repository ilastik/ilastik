from ilastik.applets.multicut.opMulticut import OpMulticut
from ilastik.applets.multicut.multicutSerializer import MulticutSerializer


def test_multicut_serializer_saves_all(
    graph,
    empty_in_memory_project_file,
):
    serializer_group = "multicut"

    op = OpMulticut(graph=graph)
    op.Beta.setValue(0.42)
    op.ProbabilityThreshold.setValue(0.23)
    op.SolverName.setValue("blah")
    serializer = MulticutSerializer(op, serializer_group)
    serializer.serializeToHdf5(empty_in_memory_project_file, empty_in_memory_project_file.name)

    assert serializer_group in empty_in_memory_project_file
    g = empty_in_memory_project_file[serializer_group]
    assert "Beta" in g and g["Beta"][()] == 0.42
    assert "ProbabilityThreshold" in g and g["ProbabilityThreshold"][()] == 0.23
    assert "SolverName" in g and g["SolverName"][()].decode() == "blah"


def test_multicut_serializer_loads_all(
    graph,
    empty_in_memory_project_file,
):
    serializer_group = "multicut"

    g = empty_in_memory_project_file.create_group(serializer_group)
    g.create_dataset("StorageVersion", data="123")
    g.create_dataset("Beta", data=0.33)
    g.create_dataset("ProbabilityThreshold", data=0.11)
    g.create_dataset("SolverName", data="lala")

    op = OpMulticut(graph=graph)
    serializer = MulticutSerializer(op, serializer_group)
    serializer.deserializeFromHdf5(empty_in_memory_project_file, empty_in_memory_project_file.name)

    assert op.ProbabilityThreshold.value == 0.11
    assert op.Beta.value == 0.33
    assert op.SolverName.value == "lala"
