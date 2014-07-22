#!/usr/bin/env python

###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2014, the ilastik developers
#                                <team@ilastik.org>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# In addition, as a special exception, the copyright holders of
# ilastik give you permission to combine ilastik with applets,
# workflows and plugins which are not covered under the GNU
# General Public License.
#
# See the LICENSE file for details. License information is also available
# on the ilastik web site at:
#		   http://ilastik.org/license.html
###############################################################################

import ilastik_main

# Special command-line control over default tmp dir
import ilastik.monkey_patches
ilastik.monkey_patches.extend_arg_parser(ilastik_main.parser)

def main():
    parsed_args, workflow_cmdline_args = ilastik_main.parser.parse_known_args()
    
    # allow to start-up by double-clicking an '.ilp' file
    if len(workflow_cmdline_args) == 1 and \
       workflow_cmdline_args[0].endswith('.ilp') and \
       parsed_args.project is None:
            parsed_args.project = workflow_cmdline_args[0]
            workflow_cmdline_args = []

    # DEBUG EXAMPLES
    #parsed_args.project='/Users/bergs/MyProject.ilp'
    #parsed_args.headless = True

    ilastik_main.main(parsed_args, workflow_cmdline_args)

if __name__ == "__main__":
    # Examples:
    # python ilastik.py --headless --project=MyProject.ilp --output_format=hdf5 raw_input.h5/volumes/data
    # python ilastik.py --playback_speed=2.0 --exit_on_failure --exit_on_success --debug --playback_script=my_recording.py
    main()
