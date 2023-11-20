"""
Module provides testing for summary report function
This function is found in web_service.py
"""
import pytest
import json
from pathlib import Path
import copy
from replay_configuration import ReplayConfigManager
from job_status import JobStatusEnum, JobStatus, JobManager
from web_service import create_summary

def test_summary_report():
    replay_config_manager = ReplayConfigManager('../../meta-data/test-simple-jobs.json')
    jobs = JobManager(replay_config_manager)
    report = create_summary(jobs)
    assert report['total_jobs'] == 3
    assert report['blocks_processed'] == 0
