from apistar import Route
from ..views import workflow

routes = [
    Route('/get-structured-info', 'GET', workflow.get_structured_info),
    Route('/get-voxels/{dataset_name}/{source_name}', 'POST', workflow.get_voxels),
    Route('/get-data/{dataset_name}/{source_name}/{format}/{roi_begin}/{roi_end}', 
          'GET', 
          workflow.get_data),
    Route('/get-n5/{dataset_name}/{source_name}/{t}/{c}/{z}/{y}/{x}', 'GET', workflow.get_n5),
    Route('/get-n5/{dataset_name}/{source_name}/attributes.json', 'GET', workflow.get_n5_attribs)
]
