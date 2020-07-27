from mpi4py import MPI
import enum
from typing import Iterable, TypeVar, Generic, Callable, Tuple
import uuid
import logging

logger = logging.getLogger(__name__)

# message payload to signal a worker that it should terminate. Value is arbitrary but should be universally unique
COMMAND_STOP_WORKER = "COMMAND_STOP_WORKER-eb23ae13-709e-4ac3-931d-99ab059ef0c2"
UNIT_OF_WORK = TypeVar("UNIT_OF_WORK")


@enum.unique
class Tags(enum.IntEnum):
    """Tags are arbitrary ints used to identify the type/purpose of a message in MPI"""

    TASK_DONE = 1  # workers send messages tagged with TASK_DONE when they finished processing a unit of work
    WORK = enum.auto()  # units of work are tagged with "WORK" and sent to workers for processing


class _Worker(Generic[UNIT_OF_WORK]):
    """A representation of a remote worker"""

    def __init__(self, comm, rank: int):
        self.comm = comm  # MPI communication channel
        self.rank = rank  # mpi worker rank, analogous to a worker ID
        self.stopped = False

    def send(self, unit_of_work: UNIT_OF_WORK):
        logger.debug(f"Sending unit_of_work {unit_of_work} to worker {self.rank}...")
        self.comm.send(unit_of_work, dest=self.rank, tag=Tags.WORK)

    def stop(self):
        self.send(COMMAND_STOP_WORKER)
        self.stopped = True


class TaskOrchestrator(Generic[UNIT_OF_WORK]):
    """Coordinates work amongst MPI processes.

    In order to use this class, applications must be launched with mpirun: e.g.: mpirun -N <num_workers> ilastik.py
    """

    def __init__(self, comm=None):
        self.comm = comm or MPI.COMM_WORLD
        self.rank = self.comm.Get_rank()
        num_workers = self.comm.size - 1
        if num_workers <= 0:
            raise ValueError("Trying to orchestrate tasks with {num_workers} workers")
        self.workers = {rank: _Worker(self.comm, rank) for rank in range(1, num_workers + 1)}

    def _get_finished_worker(self) -> _Worker[UNIT_OF_WORK]:
        status = MPI.Status()
        self.comm.recv(source=MPI.ANY_SOURCE, tag=Tags.TASK_DONE, status=status)
        return self.workers[status.Get_source()]

    def orchestrate(self, work_units: Iterable[UNIT_OF_WORK]):
        """Sends work units from work_units to workers as they become free. Usually ran in the process with mpi rank 0

        Blocks until all work units have been consumed and processed by the workers.
        Automatically terminates all workers when all work units have been consumed."""

        logger.info(f"ORCHESTRATOR: Starting orchestration of {len(self.workers)}...")
        num_busy_workers = 0
        for worker in self.workers.values():
            try:
                worker.send(next(work_units))
                num_busy_workers += 1
            except StopIteration:
                break

        while True:
            worker = self._get_finished_worker()
            try:
                worker.send(next(work_units))
            except StopIteration:
                worker.stop()
                num_busy_workers -= 1
                if num_busy_workers == 0:
                    break

        for worker in self.workers.values():
            if not worker.stopped:
                worker.stop()

    def start_as_worker(self, target: Callable[[UNIT_OF_WORK, int], None]):
        """Synchronously runs 'target' on every work unit passed in by the orchestrating intance of this class
        (usually the process with mpi rank == 0, which should be executing the 'orchestrate' method)

        Blocks until the orchestrator version of this object sends the termination command COMMAND_STOP_WORKER
        """

        logger.info(f"WORKER {self.rank}: Started")
        while True:
            status = MPI.Status()
            unit_of_work = self.comm.recv(source=MPI.ANY_SOURCE, tag=Tags.WORK, status=status)
            if unit_of_work == COMMAND_STOP_WORKER:
                break
            self.comm.send(target(unit_of_work, self.rank), dest=status.Get_source(), tag=Tags.TASK_DONE)
        logger.info(f"WORKER {self.rank}: Terminated")
