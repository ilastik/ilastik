import traceback
import StringIO
import logging

def log_exception( logger, msg=None, exc_info=None, level=logging.ERROR ):
    """
    Log the current exception to the given logger, and also log the given error message.
    If exc_info is provided, log that exception instead of the current exception provided by sys.exc_info.
    
    It is better to log exceptions this way instead of merely printing them to the console, 
    so that other logger outputs (such as log files) show the exception, too.
    """
    sio = StringIO.StringIO()
    if exc_info:
        traceback.print_exception( exc_info[0], exc_info[1], exc_info[2], file=sio )
    else:
        traceback.print_exc( file=sio )

    logger.log(level, sio.getvalue() )
    if msg:
        logger.log(level, msg )
