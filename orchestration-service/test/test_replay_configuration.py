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
    primary_key = 1
    block = BlockManager(records[0],primary_key)
    assert block is not None
    assert block._is_supported_storage_type() is True
    assert block.get_leap_deb_url().startswith("https://github.com/AntelopeIO/leap/releases/download/v")
    assert block.validate_integrity_hash("ABCD1234EFGH5678IJKL9012MNOP3456") is True

def test_initialize_block_manager_ok_with_fs():
    with open('../../meta-data/test-001-jobs.json', 'r') as f:
        records = json.load(f)
    primary_key = 2
    block = BlockManager(records[1],primary_key)
    assert block is not None
    assert block._is_supported_storage_type() is True
    assert block.get_snapshot_path() == records[1]["snapshot_path"]
    assert block.validate_integrity_hash("Z") is False

def test_initialize_block_manager_bad_record():
    with open('../../meta-data/test-001-jobs.json', 'r') as f:
        records = json.load(f)
    primary_key = 3
    with pytest.raises(KeyError):
        block = BlockManager(records[2], primary_key)
