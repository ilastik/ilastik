import logging
logger = logging.getLogger(__name__)

def extend_arg_parser(parser):
    parser.add_argument('--sys_tmp_dir', help='Override the default directory for temporary file storage.')

def init_with_args(parsed_args):
    if parsed_args.sys_tmp_dir is not None:
        import tempfile
        logger.info("Using temporary directory: {}".format( parsed_args.sys_tmp_dir ))
        tempfile.tempdir = parsed_args.sys_tmp_dir
