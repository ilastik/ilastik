from apistar import get_current_app
import os
from ..tools import log_function_call, time_function_call
from ..ilastikAPItypes import DataList

import logging


logger = logging.getLogger(__name__)


def get_data_list():
    data_folder = get_current_app()._ilastik_config.data_path
    file_list = os.listdir(data_folder)
    return file_list


@time_function_call(logger)
def list_available_data():
    file_list = get_data_list()
    return {
        'available_data': DataList(file_list),
        'message': 'List of data available on server retrieved.'
    }
