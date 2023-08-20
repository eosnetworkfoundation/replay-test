"""Module provides loading of config file in json format."""
import json
"""Module provides printing to stderr."""
import sys
"""Module provides os file name and base path."""
import os

# holds all the configuration data for the replays
# `start_block_id` first block to process
# `end_block_id` last block to process
# `snapshot_path` path to snapshot file
# `storage_type` enum s3, file
# `expected_integrity_hash` at end of block
# `nodeos_version` Maj.Min.Patch-rcN or Maj.Min.Patch-commithash
# `replay_slice_id` unique id for this replay config
#
class BlockConfigManager:
    def __init__(self, block_record, pk):
        self.start_block_id = int(block_record['start_block_id'])
        self.end_block_id = int(block_record['end_block_id'])
        self.snapshot_path = block_record['snapshot_path']
        self.storage_type = block_record['storage_type']
        self.expected_integrity_hash = block_record['expected_integrity_hash']
        self.leap_version = block_record['leap_version']
        self.replay_slice_id = pk

    def get_snapshot_path(self):
        if not self._is_supported_storage_type():
            raise ValueError("Error BM001: storage type {self.storage_type} not supported")
        return self.snapshot_path

    def _is_supported_storage_type(self):
        return self.storage_type in ["s3","filesystem","fs"]

    def get_leap_deb_url(self):
        os="ubuntu22.04"
        repo="AntelopeIO/leap"
        service="github.com"
        return f"https://{service}/{repo}/releases/download/v{self.leap_version}/leap_{self.leap_version}-{os}_amd64.deb"

    def validate_integrity_hash(self, computed_integrity_hash):
        return computed_integrity_hash == self.expected_integrity_hash

# Read only class to access configuration records for a replay
# Loads the json configuration
# Creates the primary key for blocks
# provides accessor methods
# single member `records` array of BlockConfig
class ReplayConfigManager:
    def __init__(self, json_file_path):
        with open(json_file_path, 'r') as f:
            records = json.load(f)
        self.records = []
        self.current = 0
        if len(records) < 1:
            print(f"Error RM001 tried to load empty jobs file ", file=sys.stderr)
        # init the pk
        generated_id = 1
        for block in records:
            self.records.append(BlockConfigManager(block, generated_id))
            generated_id += 1

    def __iter__(self):
        return self

    def __next__(self):
        if self.current >= len(self.records):
            self.current = 0
            raise StopIteration
        self.current += 1
        return self.records[self.current-1]

    def get(self, primary_key):
        for record in self.records:
            if record.replay_slice_id == primary_key:
                return record
        return None

    def return_record_by_start_block_id(self, start_block_id):
        for record in self.records:
            if record.start_block_id == start_block_id:
                return record
        return None

    def return_record_by_end_block_id(self, end_block_id):
        for record in self.records:
            if record.end_block_id == end_block_id:
                return record
        return None
