from mpi4py import MPI
from threading import Thread
import enum
from typing import Generator, TypeVar, Generic, Callable, Tuple
import uuid

END = "END-eb23ae13-709e-4ac3-931d-99ab059ef0c2"
TASK_DATUM = TypeVar("TASK_DATUM")


@enum.unique
class Tags(enum.IntEnum):
    TASK_DONE = 13
    TO_WORKER = enum.auto()


class _Worker(Generic[TASK_DATUM]):
    def __init__(self, comm, rank: int):
        self.comm = comm
        self.rank = rank
        self.stopped = False

    def send(self, datum: TASK_DATUM):
        print(f"Sending datum {datum} to worker {self.rank}...")
        self.comm.send(datum, dest=self.rank, tag=Tags.TO_WORKER)

    def stop(self):
        self.send(END)
        self.stopped = True


class TaskOrchestrator(Generic[TASK_DATUM]):
    def __init__(self, comm=None):
        self.comm = comm or MPI.COMM_WORLD
        self.rank = self.comm.Get_rank()
        num_workers = self.comm.size - 1
        if num_workers <= 0:
            raise Exception("Trying to orchestrate tasks with no workers!!!")
        self.workers = {rank: _Worker(self.comm, rank) for rank in range(1, num_workers + 1)}

    def get_finished_worker(self) -> _Worker[TASK_DATUM]:
        status = MPI.Status()
        self.comm.recv(source=MPI.ANY_SOURCE, tag=Tags.TASK_DONE, status=status)
        return self.workers[status.Get_source()]

    def orchestrate(self, task_data: Generator[TASK_DATUM, None, None]):
        print(f"ORCHESTRATOR: Starting orchestration of {len(self.workers)}...")
        num_busy_workers = 0
        for worker in self.workers.values():
            try:
                worker.send(next(task_data))
                num_busy_workers += 1
            except StopIteration:
                break

        while True:
            worker = self.get_finished_worker()
            try:
                worker.send(next(task_data))
            except StopIteration:
                worker.stop()
                num_busy_workers -= 1
                if num_busy_workers == 0:
                    break

        for worker in self.workers.values():
            if not worker.stopped:
                worker.stop()

    def start_as_worker(self, target: Callable[[TASK_DATUM, int], None]):
        print(f"WORKER {self.rank}: Started")
        while True:
            status = MPI.Status()
            datum = self.comm.recv(source=MPI.ANY_SOURCE, tag=Tags.TO_WORKER, status=status)
            if datum == END:
                break
            self.comm.send(target(datum, self.rank), dest=status.Get_source(), tag=Tags.TASK_DONE)
        print(f"WORKER {self.rank}: Terminated")
