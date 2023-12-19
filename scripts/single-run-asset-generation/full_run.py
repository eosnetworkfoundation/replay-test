"""Single node run over entire history with snapshot spaced at specified block heights"""
import sys
import subprocess
import unittest
import os

# --blocks-log-stride = 2000000
# --max-retained-block-files = 512
# --blocks-retained-dir = retained

class S3Interface:
    """cli commands to interfaces with S3 storage"""
    @staticmethod
    def build_s3_loc(bucket, path):
        """create the path to the s3 location"""
        return f"s://{bucket.strip('/')}/{path}"

    @staticmethod
    def exists(bucket, s3_path):
        """checks if a file exists in cloud store"""
        s3_file_exists = ["aws", "s3api", "head-object", \
            "--bucket", bucket, "--key", s3_path]
        exists_result = subprocess.run(s3_file_exists, \
            check=False, capture_output=True, text=True)
        return exists_result.returncode == 0

    @staticmethod
    def upload(bucket, path, file):
        """uploades file to cloud store"""
        s3_loc = S3Interface.build_s3_loc(bucket, path)
        upload_cmd = ["aws", "s3", "cp", file, s3_loc]
        upload_result = subprocess.run(upload_cmd, \
            check=False, capture_output=True, text=True)
        if upload_result.returncode != 0:
            print(f"upload to {s3_loc} failed with {upload_result.stderr}", file=sys.stderr)
            return {'success': False}
        return {'success': True}


    @staticmethod
    def download(download_file, url):
        """downloads a file from cloud store"""
        download_cmd = ["curl", "-s", "-o", download_file, url]
        download_result = subprocess.run(download_cmd, \
            check=False, capture_output=True, text=True)
        if download_result.returncode != 0:
            print(f"download of {url} failed with {download_result.stderr}", file=sys.stderr)
            return {'success': False}
        return {'success': True}

    @staticmethod
    def compress(file):
        """compresses a local file"""
        compress_cmd = ["zstd", file]
        compress_result = subprocess.run(compress_cmd, \
            check=False, capture_output=True, text=True)
        if compress_result.returncode != 0:
            print(f"compressing {file} failed with {compress_result.stderr}", file=sys.stderr)
            return {'success': False, 'file': None}
        return {'success': True, 'file': file + '.zst'}

class Nodeos:
    """commands for working with nodeos"""
    @staticmethod
    def start_sync(stop_block_height):
        """start nodeos command"""
        cmd = ['nodeos']

    @staticmethod
    def start_readonly():
        """start nodeos in readonly mode"""
        cmd = ['nodoes']

    @staticmethod
    def snapshot(block_height):
        """create a snapshot"""
        cmd = ['curl']

class Manifest:
    """opens manifest file with three columns
    start, end, span
    parses and expands manifest if start and end range contain spans"""
    def __init__(self, file):
        self.manifest = self.parse(file)
        self.manifest = self.expand()

    def parse(self,file):
        """open file , parse and sort"""
        unordered_manifest = {}
        with open(file, 'r', encoding='utf-8') as manifest_file:
            for line in manifest_file:
                clean = line.strip()
                start = int(clean.split('\t')[0])
                end = int(clean.split('\t')[1])
                span = int(clean.split('\t')[2])
                unordered_manifest[start] = {'start_num': start, 'end_num':end, 'span': span }
        return unordered_manifest

    def expand(self):
        """some start and end ranges need to be broken up into smaller chunks to optimize loading"""
        buffer_multiple = 1.1
        new_entries = {}
        for outer_record in self.manifest.values():
            # start + (span * 1.1) is less then end, we need to break up this record
            # otherwise the record is fine and we leave it alone
            if outer_record['start_num']\
                + (outer_record['span'] * buffer_multiple) < outer_record['end_num']:
                inner_start = int(outer_record['start_num'])
                span = outer_record['span']
                # loop until the range is small enough
                while inner_start < outer_record['end_num']:
                    inner_end = inner_start + span
                    # explicit set end when it exceeds the outer record end
                    if inner_start + (span * buffer_multiple) > outer_record['end_num']:
                        inner_end = outer_record['end_num']
                    # create or update a new record
                    new_entries[inner_start]\
                        = {'start_num': inner_start, 'end_num':inner_end, 'span': span }
                    # start a new inner range
                    inner_start = int(inner_end)
        if new_entries:
            for key, new_rec in new_entries.items():
                self.manifest[key] = new_rec
        return {k: self.manifest[k] for k in sorted(self.manifest)}

    def is_valid(self):
        """one more pass through to validate"""
        max_block_key = 0
        for key in self.manifest.keys():
            if key > max_block_key:
                max_block_key = key
        max_block_height = self.manifest[max_block_key]['end_num']
        for record in self.manifest.values():
            # except for very last block make sure every entry is contiguous
            # continguous every end block is linked to another start block
            if record['end_num'] != max_block_height and record['end_num'] not in self.manifest:
                print(f"failed to find record matching {record['end_num']}", file=sys.stderr)
                return False
        return True

    def __str__(self):
        return_str = ""
        for record in self.manifest.values():
            return_str += f"{record['start_num']}\t{record['end_num']}\t{record['span']}\n"
        return return_str

class TestFileParsing(unittest.TestCase):
    """unittest class for testing manifest class"""
    @classmethod
    def setUpClass(cls):
        # Create a sample file
        cls.sample_file_path = 'sample_test_file.tsv'
        with open(cls.sample_file_path, 'w', encoding='utf-8') as file:
            file.write("0\t500000\t500000\n")
            file.write("500000\t2000000\t500000\n")
            file.write("2000000\t2500000\t500000\n")
            file.write("2500000\t3000000\t400000\n")

    @classmethod
    def tearDownClass(cls):
        # Clean up: Remove the sample file after tests
        os.remove(cls.sample_file_path)

    def test_manifest(self):
        """test the manifest using faked file"""
        test_manifest = Manifest('sample_test_file.tsv')
        if test_manifest.is_valid():
            print(test_manifest)
            print("Valid Manifest")
        else:
            print(test_manifest)
            print("Test Failed: Manifest entries are not contiguous")
        if len(test_manifest.manifest) == 7:
            print("Manifest Has Correct Number of Records")
        else:
            print(f"Test Failed Manifest has {len(test_manifest.manifest)} records expected 7")

if __name__ == '__main__':
    unittest.main()
