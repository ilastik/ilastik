def init_with_args(parsed_args):
    if parsed_args.sys_tmp_dir is not None:
        import tempfile
        tempfile.tempdir = parsed_args.sys_tmp_dir
