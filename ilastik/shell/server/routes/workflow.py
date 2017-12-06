from apistar import Route
from ..views import workflow

routes = [
    Route('/get-structured-info', 'GET', workflow.get_structured_info),
    Route('/get-voxels/{dataset_name}/{source_name}', 'POST', workflow.get_voxels),
    Route('/get-data/{dataset_name}/{source_name}/{format}/{roi_begin}/{roi_end}', 
          'GET', 
          workflow.get_data)
]
