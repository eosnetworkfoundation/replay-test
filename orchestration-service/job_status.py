from datetime import datetime
from enum import Enum

class JobStatusEnum(Enum):
    WAITING_4_WORKER = "waiting_4_worker"
    STARTED = "started"
    WORKING = "working"
    FINISHED = "finished"
    ERROR = "error"
    TIMEOUT = "timeout"

# JobsManager a dictionary that holds JobStatus
# primary key is an integer `job_id`
# has the following properties
# `replay_slice_id` integer FK linked to `BlockManger.replay_slice_id`
# `status` enum of waiting_4_worker, started, working, finished, error, timeout
#     initialized to waiting_4_worker
# `last_block_processed` block id of last block processed
#     initialized to 0
# `start_time` date time job started
#     initialized to now
# `end_time` date time job completed
#     initialized None
# `actual_integrity_hash` hash once last block has been reached
#     initialized to None
# The class in inialized from an array, whose elements have a property `replay_slice_id`
class JobStatus:
    def __init__(self, config):
        self.job_id = id(self)  # Using memory address as a simple unique identifier
        self.slice_config = config
        self.status = JobStatusEnum.WAITING_4_WORKER
        self.last_block_processed = 0
        self.start_time = datetime.now()
        self.end_time = None
        self.actual_integrity_hash = None

    def __repr__(self):
        return (f"JobStatus(job_id={self.job_id}, replay_slice_id={self.slice_config.replay_slice_id}, "
                f"status={self.status}, last_block_processed={self.last_block_processed}, "
                f"start_time={self.start_time}, end_time={self.end_time}, "
                f"actual_integrity_hash={self.actual_integrity_hash})")

#
# JobStatusManager Class
class JobManager:
    def __init__(self, replay_configs):
        self.jobs = {}
        for slice_config in replay_configs:
            job_status = JobStatus(slice_config)
            self.jobs[job_status.job_id] = job_status

    def get_job(self, job_id):
        return self.jobs.get(job_id)

    # no op hook for future data persistance
    def set_job(self, job):
        pass
    

    def get_next_job(self):
        for job_id in self.jobs:
            if self.jobs[job_id].status == JobStatusEnum.WAITING_4_WORKER:
                return self.jobs[job_id]
        return None
