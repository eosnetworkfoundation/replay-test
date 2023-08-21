"""Module provides now and job status"""
from datetime import datetime
from enum import Enum

# pylint: disable=too-few-public-methods
class JobStatusEnum(Enum):
    """Job Lifecyle as Enum"""
    WAITING_4_WORKER = "waiting_4_worker"
    STARTED = "started"
    WORKING = "working"
    FINISHED = "finished"
    ERROR = "error"
    TIMEOUT = "timeout"

class JobStatus:
    """
    JobsManager a dictionary that holds JobStatus
    primary key is an integer `job_id`
    has the following properties
    `replay_slice_id` integer FK linked to `BlockManger.replay_slice_id`
    `status` enum of waiting_4_worker, started, working, finished, error, timeout
        initialized to waiting_4_worker
    `last_block_processed` block id of last block processed
        initialized to 0
    `start_time` date time job started
        initialized to now
    `end_time` date time job completed
        initialized None
    `actual_integrity_hash` hash once last block has been reached
        initialized to None
    The class in inialized from an array, whose elements have a property `replay_slice_id`
    """
    def __init__(self, config):
        self.job_id = id(self)  # Using memory address as a simple unique identifier
        self.slice_config = config
        self.status = JobStatusEnum.WAITING_4_WORKER
        self.last_block_processed = 0
        self.start_time = datetime.now()
        self.end_time = None
        self.actual_integrity_hash = None

    def __repr__(self):
        return (f"JobStatus(job_id={self.job_id}, "
                f"replay_slice_id={self.slice_config.replay_slice_id}, "
                f"status={self.status}, "
                f"last_block_processed={self.last_block_processed}, "
                f"start_time={self.start_time}, end_time={self.end_time}, "
                f"actual_integrity_hash={self.actual_integrity_hash})")


class JobManager:
    """Holds Jobs and manages persistance"""

    def __init__(self, replay_configs):
        self.jobs = {}
        for slice_config in replay_configs:
            job_status = JobStatus(slice_config)
            self.jobs[job_status.job_id] = job_status

    def get_job(self, job_id):
        """Return job by id"""
        return self.jobs.get(job_id)

    def get_all(self):
        """Return all jobs"""
        return self.jobs

    # pylint: disable=unnecessary-pass
    def set_job(self, job):
        """no op hook for future data persistance"""
        pass

    def get_next_job(self):
        """get a job that needs a worker"""
        for job in self.jobs.values():
            if job.status == JobStatusEnum.WAITING_4_WORKER:
                return job
        return None
