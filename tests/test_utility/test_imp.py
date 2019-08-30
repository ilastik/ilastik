import subprocess
import textwrap


def run_script(src: str) -> subprocess.CompletedProcess:
    src = textwrap.dedent(src).strip().replace("\n", "; ")
    return subprocess.run(["python", "-c", src], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)


def assert_script_ok(src: str):
    proc = run_script(src)
    # Use explicit exception to prevent pytest from rewriting an error message.
    if proc.returncode != 0:
        raise AssertionError(proc.stdout)


def assert_script_fail(src: str):
    proc = run_script(src)
    assert proc.returncode != 0


def test_blacklist_blocks_blacklisted_module():
    src = """\
        from ilastik.utility.imp import Blacklist
        Blacklist("spam").install()
        import spam
    """
    assert_script_fail(src)


def test_blacklist_allows_non_blacklisted_module():
    src = """\
        from ilastik.utility.imp import Blacklist
        Blacklist("spam").install()
        import turtle
    """
    assert_script_ok(src)


def test_blacklist_prevents_double_installation():
    src = """\
        from ilastik.utility.imp import Blacklist
        blacklist = Blacklist()
        blacklist.install()
        blacklist.install()
    """
    assert_script_fail(src)


def test_blacklist_detects_already_imported_modules_during_installation():
    src = """\
        from ilastik.utility.imp import Blacklist
        import turtle
        Blacklist("turtle").install()
    """
    assert_script_fail(src)
