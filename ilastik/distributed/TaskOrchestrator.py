from mpi4py import MPI
from threading import Thread
import enum
from typing import Generator, TypeVar, Generic, Callable

TASK_DATUM = TypeVar("TASK_DATUM")


class TaskOrchestrator(Generic[TASK_DATUM]):
    @enum.unique
    class Tags(enum.IntEnum):
        TASK_DONE = 13
        TO_WORKER = enum.auto()

    END = "END"

    def __init__(self, comm=None):
        self.comm = comm or MPI.COMM_WORLD
        self.rank = self.comm.Get_rank()
        self.num_workers = self.comm.size - 1

    def orchestrate(self, task_data: Generator[TASK_DATUM, None, None]):
        print(f"ORCHESTRATOR: Starting orchestration of {self.num_workers}...")
        stopped_workers = self.num_workers
        for worker_idx in range(1, self.num_workers + 1):
            try:
                datum = next(task_data)
                self.comm.send(datum, dest=worker_idx, tag=self.Tags.TO_WORKER)
                stopped_workers -= 1
                print(f"Sent datum {datum} to worker {worker_idx}...")
            except StopIteration:
                break

        while True:
            status = MPI.Status()
            self.comm.recv(source=MPI.ANY_SOURCE, tag=self.Tags.TASK_DONE, status=status)
            worker_idx = status.Get_source()

            try:
                self.comm.send(next(task_data), dest=worker_idx, tag=self.Tags.TO_WORKER)
            except StopIteration:
                self.comm.send(self.END, dest=worker_idx, tag=self.Tags.TO_WORKER)
                stopped_workers += 1
                if stopped_workers == self.num_workers:
                    break

    def start_as_worker(self, target: Callable[[TASK_DATUM, int], None]):
        print(f"WORKER {self.rank}: Started")
        while True:
            status = MPI.Status()
            datum = self.comm.recv(source=MPI.ANY_SOURCE, tag=self.Tags.TO_WORKER, status=status)
            if datum == self.END:
                break
            self.comm.send(target(datum, self.rank), dest=status.Get_source(), tag=self.Tags.TASK_DONE)
        print(f"WORKER {self.rank}: Terminated")
