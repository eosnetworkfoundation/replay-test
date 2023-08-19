"""Module provides testing."""
import pytest
"""Module provides loading of config file in json format."""
import json
"""Module provides marshling replay records."""
from replay_configuration import ReplayManager
"""Module provides building config for replay node from json meta-data."""
from replay_configuration import BlockManager

def test_initialize_replay_manager():
    manager = ReplayManager('../../meta-data/test-simple-jobs.json')
    assert manager is not None

def test_initialize_block_manager_ok_with_s3():
    with open('../../meta-data/test-001-jobs.json', 'r') as f:
        records = json.load(f)
    block = BlockManager(records[0])
    assert block is not None
    assert block._is_supported_storage_type() is True

def test_initialize_block_manager_ok_with_fs():
    with open('../../meta-data/test-001-jobs.json', 'r') as f:
        records = json.load(f)
    block = BlockManager(records[1])
    assert block is not None
    assert block._is_supported_storage_type() is True
    assert block.download_snapshot() == records[1]["snapshot_path"]

def test_initialize_block_manager_bad_record():
    with open('../../meta-data/test-001-jobs.json', 'r') as f:
        records = json.load(f)
    with pytest.raises(KeyError):
        block = BlockManager(records[2])