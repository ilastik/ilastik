import argparse
from collections import namedtuple
import logging
logger = logging.getLogger(__name__)


def _update_sys_temp(custom_tmp_dir):
    """
    Override the default directory that the python tempfile module uses for creating temporary files.
    """
    import tempfile
    logger.info( "Using temporary directory: {}".format( custom_tmp_dir ) )
    tempfile.tempdir = custom_tmp_dir

def extend_arg_parser(parser):
    """
    Add all monkey_patch options to the given arg parser.
    """
    for option, help in monkey_patch_options.items():
        parser.add_argument('--' + option, help=help, required=False)

def apply_args(args):
    """
    Examine the given command-line arguments and apply any settings we recognize as options for this module.
    """
    parser = argparse.ArgumentParser()
    extend_arg_parser(parser)
    namespace, remaining_args = parser.parse_known_args( args )
    apply_setting_dict( namespace.__dict__ )

    return remaining_args

def apply_setting_dict( option_dict ):
    """
    Examine the given dict of { setting name : setting value } options,
    and apply any settings we recognize as options for this module.
    """
    for setting, value in option_dict.items():
        if setting in monkey_patch_options:
            monkey_patch_options[setting].update_func( value )

OptionAction = namedtuple('OptionInfo', ['help', 'update_func'])
monkey_patch_options = { 'sys_tmp_dir' : OptionAction( help='Override the default directory for temporary file storage.',
                                                       update_func=_update_sys_temp ) }


