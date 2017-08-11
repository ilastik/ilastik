from __future__ import division
from builtins import object
import os
import psutil

this_process = psutil.Process(os.getpid())

class RamMeasurementContext(object):
    """
    Simple context manager to track the difference in this processes's 
    resident memory usage between the start and stop of the context.
    """
    def __init__(self):
        self.ram_mb_at_enter = None
        self.ram_mb_at_exit = None
        self.ram_increase_mb = None
    
    def __enter__(self):
        self.ram_mb_at_enter = (float(this_process.memory_info().rss) / 1e6)
        return self
    
    def __exit__(self, *args):
        self.ram_mb_at_exit = (float(this_process.memory_info().rss) / 1e6)
        self.ram_increase_mb = self.ram_mb_at_exit - self.ram_mb_at_enter
