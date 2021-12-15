from functools import singledispatch
from ilastik.experimental import parser
from ._pipelines import get_pipeline_for_project


def from_project_file(path):
    project: parser.PixelClassificationProject

    with parser.IlastikProject(path, "r") as project:
        if not project.ready_for_prediction:
            raise ValueError("not sufficient data in project file for prediction")

        pipeline = get_pipeline_for_project(project)

    return pipeline
