"""Module provides loading of config file in json format."""
import json
"""Module provides printing to stderr."""
import sys
"""Module provides execution of shell commands ."""
import subprocess
"""Module provides os file name and base path."""
import os

# holds all the configuration data for the replays
# `start_block_id` first block to process
# `end_block_id` last block to process
# `snapshot_path` path to snapshot file
# `storage_type` enum s3, file
# `expected_integrity_hash` at end of block
# `nodeos_version` Maj.Min.Patch-rcN or Maj.Min.Patch-commithash
class BlockManager:
    def __init__(self, block_record):
        self.start_block_id = int(block_record['start_block_id'])
        self.end_block_id = int(block_record['end_block_id'])
        self.snapshot_path = block_record['snapshot_path']
        self.storage_type = block_record['storage_type']
        self.expected_integrity_hash = block_record['expected_integrity_hash']
        self.nodeos_version = block_record['nodeos_version']

    def download_snapshot(self):
        if not self._is_supported_storage_type():
            raise ValueError("Error BM001: storage type {self.storage_type} not supported")
        if self.storage_type == "s3":
            try:
                subprocess.check_call(["aws", "s3", "cp", self.snapshot_path, "~/snapshot/"])
            except subprocess.CalledProcessError:
                raise Exception("Error BM003 copy from s3 failed")
            return "~/snapshot/" + os.path.basename(self.snapshot_path)

        if self.storage_type in ["fs","filesystem"]:
            return self.snapshot_path

    def _is_supported_storage_type(self):
        return self.storage_type in ["s3","filesystem","fs"]

    def download_nodeos(self):
        # Similarly, use appropriate method to download the nodeos version.
        # For the purpose of this example, we're just printing a message.
        print(f"Downloading nodeos version: {self.nodeos_version}")

    def validate_integrity_hash(self, computed_integrity_hash):
        return computed_integrity_hash == self.expected_integrity_hash

class ReplayManager:
    def __init__(self, json_file_path):
        with open(json_file_path, 'r') as f:
            records = json.load(f)
        self.records = []
        if len(records) < 1:
            print(f"Error RM001 tried to load empty jobs file ", file=sys.stderr)
        for block in records:
            self.records.append(BlockManager(block))

    def return_record_by_start_block_id(self, start_block_id):
        for record in self.records:
            if record['start_block_id'] == start_block_id:
                return record
        return None

    def return_record_by_end_block_id(self, end_block_id):
        for record in self.records:
            if record['end_block_id'] == end_block_id:
                return record
        return None
