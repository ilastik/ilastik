# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# Copyright 2011-2014, the ilastik developers

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
    for option, optact in monkey_patch_options.items():
        parser.add_argument('--' + option, help=optact.help, required=False)

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
        if setting in monkey_patch_options and value is not None:
            monkey_patch_options[setting].update_func( value )

OptionAction = namedtuple('OptionInfo', ['help', 'update_func'])
monkey_patch_options = { 'sys_tmp_dir' : OptionAction( help='Override the default directory for temporary file storage.',
                                                       update_func=_update_sys_temp ) }


