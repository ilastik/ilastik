from apistar import get_current_app
from ..tools import log_function_call, time_function_call


import logging
logger = logging.getLogger(__name__)


@time_function_call(logger=logger)
def get_structured_info():
    dataset_names, json_states = get_current_app()._ilastik_api.get_structured_info()
    resp = {
        'states': json_states,
        'image_names': dataset_names,
        'message': 'Structured info retrieval successful'
    }
    return resp
