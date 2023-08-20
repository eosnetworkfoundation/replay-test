"""Module provides testing."""
import pytest
"""Module provides loading of config file in json format."""
import json
"""Module provides marshling replay records."""
from replay_configuration import ReplayConfigManager
"""Module provides building config for replay node from json meta-data."""
from replay_configuration import BlockConfigManager
"""Module provides job manager class."""
from job_status import JobManager
"""Module provides job status class."""
from job_status import JobStatus
"""Module provides job statuses as enum."""
from job_status import JobStatusEnum

# initialize replay configs once and use in many tests
@pytest.fixture(scope="module")
def setup_module():
    # Your setup code here
    print("Setting up Test Jobs...")
    return ReplayConfigManager('../../meta-data/test-simple-jobs.json')

# build a manager and get a job
def test_initialize_job_manager(setup_module):
    manager = JobManager(setup_module)
    assert manager is not None

# replay_configs has only 3 items
# only 3 jobs, after getting them 3 times, the 4th job request should be None
def test_exhaust_jobs(setup_module):
    manager = JobManager(setup_module)
    for _ in range(3):
        job = manager.get_next_job()
        assert job.status == JobStatusEnum.WAITING_4_WORKER
        job.status = JobStatusEnum.STARTED
        manager.set_job(job)
        assert job is not None
    job = manager.get_next_job()
    assert job is None
