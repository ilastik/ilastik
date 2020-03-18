from __future__ import print_function
import signal
import functools
import threading
import platform


class TimeoutError(Exception):
    def __init__(self, seconds):
        super(TimeoutError, self).__init__(seconds)


def fail_after_timeout(seconds):
    """
    Returns a decorator that causes the wrapped function to asynchronously
    fail with a TimeoutError exception if the function takes too long to execute.

    TODO: Right now, timeout must be an int.  If we used signal.setitimer() instead
          of signal.alarm, we could probably support float, but I don't care right now.

    CAVEATS: Apparently signal.alarm() can only interrupt Python bytecode, so it can't
             be used to detect timeouts during C-functions, such as threading.Lock.acquire(), for example.
             Also, the function you're wrapping must only be called from the main thread.

    EXAMPLE: See example usage at the bottom of this file.
    """
    assert isinstance(seconds, int), "signal.alarm() requires an int"

    def decorator(func):
        if platform.system() == "Windows":
            # Windows doesn't support SIGALRM
            # Therefore, on Windows, we let this decorator be a no-op.
            return func

        def raise_timeout(signum, frame):
            raise TimeoutError(seconds)

        @functools.wraps(func)
        def fail_after_timeout_wrapper(*args, **kwargs):
            assert threading.current_thread().name == "MainThread", (
                "Non-Main-Thread detected: This decorator relies on the signal"
                " module, which may only be used from the MainThread"
            )

            old_handler = signal.getsignal(signal.SIGALRM)
            signal.signal(signal.SIGALRM, raise_timeout)

            # Start the timer, check for conflicts with any previous timer.
            old_alarm_time_remaining = signal.alarm(seconds)
            if old_alarm_time_remaining != 0:
                raise Exception("Can't use fail_after_timeout if you're already using signal.alarm for something else.")

            try:
                return func(*args, **kwargs)
            finally:
                # Restore old handler, clear alarm
                signal.signal(signal.SIGALRM, old_handler)
                signal.alarm(0)

        fail_after_timeout_wrapper.__wrapped__ = func  # Emulate python 3 behavior of @functools.wraps
        return fail_after_timeout_wrapper

    return decorator


if __name__ == "__main__":
    import time

    @fail_after_timeout(2)
    def long_running_function():
        time.sleep(3)

    try:
        long_running_function()
    except TimeoutError as ex:
        print("Got TimeoutError, as expected")
    else:
        assert False, "Expected to catch a TimeoutError! Why didn't that happen?"
