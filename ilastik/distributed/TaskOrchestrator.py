from mpi4py import MPI
from threading import Thread
import enum


class TaskOrchestrator(object):
    @enum.unique
    class Tags(enum.IntEnum):
        TASK_DONE = 13
        TO_WORKER = enum.auto()

    END = "END"

    def __init__(self, slice_iterator, producer_also_consumes=True, comm=None):
        self.comm = comm or MPI.COMM_WORLD
        self.rank = self.comm.Get_rank()
        self.slice_iterator = slice_iterator
        self.num_workers = self.comm.size
        if not producer_also_consumes:
            self.num_workers -= 1

    def start_background_producer_if_leader(self):
        if self.rank == 0:
            self.start_background_producer()

    def start_background_producer(self):
        print(f"~~~~~~>> Starting a producer to manage {self.num_workers} workers")
        Thread(target=self._orchestrate).start()

    def _orchestrate(self):
        print("Starting orchestration...")
        stopped_workers = self.num_workers
        for worker_idx in range(self.num_workers):
            try:
                next_slice = next(self.slice_iterator)
                self.comm.send(next_slice, dest=worker_idx, tag=self.Tags.TO_WORKER)
                stopped_workers -= 1
                print(f"Sent slice {next_slice} to worker {worker_idx}...")
            except StopIteration:
                break

        while True:
            status = MPI.Status()
            print("trying to receive........................")
            self.comm.recv(source=MPI.ANY_SOURCE, tag=self.Tags.TASK_DONE, status=status)
            worker_idx = status.Get_source()
            print(f"==> task received from {worker_idx}.")

            try:
                self.comm.send(next(self.slice_iterator), dest=worker_idx, tag=self.Tags.TO_WORKER)
                print(f"Dispatched new job to worker {worker_idx}")
            except StopIteration:
                self.comm.send(self.END, dest=worker_idx, tag=self.Tags.TO_WORKER)
                stopped_workers += 1
                if stopped_workers == self.num_workers:
                    break

    def startForegroundWorker(self, target):
        while True:
            status = MPI.Status()
            data = self.comm.recv(source=MPI.ANY_SOURCE, tag=self.Tags.TO_WORKER, status=status)
            if data == self.END:
                break
            self.comm.send(target(data, self.rank), dest=status.Get_source(), tag=self.Tags.TASK_DONE)
        print(f"WORKER {self.rank}: Terminated")
