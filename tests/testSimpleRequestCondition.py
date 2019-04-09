from builtins import range
from builtins import object
import sys
import time
import random
import logging
from functools import partial
from lazyflow.request import Request, SimpleRequestCondition

logger = logging.getLogger("tests.testSimpleRequestCondition")


class TestSimpleRequestCondition(object):
    def testBasic(self):
        """
        Test the SimpleRequestCondition, which is like threading.Condition, but with a subset of the functionality.
        (See the docs for details.)
        """
        # num_workers = Request.global_thread_pool.num_workers
        # Request.reset_thread_pool(num_workers=1)
        N_ELEMENTS = 100

        # It's tempting to simply use threading.Condition here,
        #  but that doesn't quite work if the thread calling wait() is also a worker thread.
        # (threading.Condition uses threading.Lock() as it's 'waiter' lock, which blocks the entire worker.)
        # cond = threading.Condition( RequestLock() )
        cond = SimpleRequestCondition()

        produced = []
        consumed = []

        def wait_for_all():
            def f(i):
                time.sleep(0.2 * random.random())
                with cond:
                    produced.append(i)
                    cond.notify()

            reqs = []
            for i in range(N_ELEMENTS):
                req = Request(partial(f, i))
                reqs.append(req)

            for req in reqs:
                req.submit()

            _consumed = consumed
            with cond:
                while len(_consumed) < N_ELEMENTS:
                    while len(_consumed) == len(produced):
                        cond.wait()
                    logger.debug("copying {} elements".format(len(produced) - len(consumed)))
                    _consumed += produced[len(_consumed) :]

        # Force the request to run in a worker thread.
        # This should catch failures that can occur if the Condition's "waiter" lock isn't a request lock.
        req = Request(wait_for_all)
        req.submit()

        # Now block for completion
        req.wait()

        logger.debug("produced: {}".format(produced))
        logger.debug("consumed: {}".format(consumed))
        assert set(consumed) == set(range(N_ELEMENTS)), "Expected set(range(N_ELEMENTS)), got {}".format(consumed)

        # Request.reset_thread_pool(num_workers)


if __name__ == "__main__":
    import sys

    sys.argv.append("--nocapture")  # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture")  # Don't set the logging level to DEBUG.  Leave it alone.

    import nose

    # Logging is OFF by default when running from command-line nose, i.e.:
    # nosetests thisFile.py)
    # but ON by default if running this test directly, i.e.:
    # python thisFile.py
    formatter = logging.Formatter("%(levelname)s %(name)s %(message)s")
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    logging.getLogger().addHandler(handler)
    logger.setLevel(logging.DEBUG)

    ret = nose.run(defaultTest=__file__)
    if not ret:
        sys.exit(1)
