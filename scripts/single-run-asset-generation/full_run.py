"""Single node run over entire history with snapshot spaced at specified block heights"""
import sys
import subprocess
import argparse
import logging
from re import sub
import json
import requests
import tomli
import numpy

# --blocks-log-stride = 2000000
# --max-retained-block-files = 512
# --blocks-retained-dir = retained
with open("./scripts/single-run-asset-generation/env.toml", "rb") as f:
    env_data = tomli.load(f)

CLOUD_STORE = env_data['CLOUD_STORE']
CLOUD_SOURCE_TYPE = env_data['CLOUD_SOURCE_TYPE']
CLOUD_BLOCK_DIR = env_data['CLOUD_SOURCE_TYPE'] + env_data['CLOUD_BLOCK_DIR']
CLOUD_SNAPSHOP_DIR = env_data['CLOUD_SOURCE_TYPE'] + env_data['CLOUD_SNAPSHOP_DIR']
REPLAY_CLIENT_DIR = env_data['REPLAY_CLIENT_DIR']
CONFIG_DIR = env_data['CONFIG_DIR']
NODEOS_DIR = env_data['NODEOS_DIR']
BLOCKS_RETAINED_DIR = env_data['NODEOS_DIR'] + env_data['BLOCKS_RETAINED_DIR']
SNAPSHOT_DIR = env_data['NODEOS_DIR'] + env_data['SNAPSHOT_DIR']
BASE_URL = env_data['BASE_URL']

# pylint: disable=too-few-public-methods
# pylint: disable=R1732
class S3Interface:
    """cli commands to interfaces with S3 storage"""
    @staticmethod
    def build_s3_loc(bucket, path):
        """create the path to the s3 location"""
        return f"s3://{bucket.strip('/')}/{path}"

    @staticmethod
    def exists(bucket, s3_path):
        """checks if a file exists in cloud store"""
        s3_file_exists = ["aws", "s3api", "head-object", \
            "--bucket", bucket, "--key", s3_path]
        exists_result = subprocess.run(s3_file_exists, \
            check=False, capture_output=True, text=True)
        return exists_result.returncode == 0

    @staticmethod
    def list(bucket, s3_path, name_only=False):
        """list all files in a directory"""

        s3_dir_path = S3Interface.build_s3_loc(bucket,s3_path)
        s3_list = ["aws", "s3", "ls", s3_dir_path]
        s3_list_result = subprocess.run(s3_list, \
            stdout=subprocess.PIPE, check=False, text=True)
        listing = []

        if s3_list_result.returncode == 0:

            file_list = s3_list_result.stdout.split('\n')
            # Remove any empty strings from the list
            file_list = [file for file in file_list if file]

            for record in file_list:
                logging.debug("file list %s", record)
                # need 4 items, skip if too few
                if len(record.split()) < 4:
                    continue

                datetime = record.split()[0] + " " \
                    + record.split()[1]
                size = record.split()[2]
                name = record.split()[3]

                if name_only:
                    listing.append(name)
                else:
                    listing.append({
                        "datetime": datetime,
                        "size": size,
                        "name": name
                    })
        else:
            logging.error("listing for %s failed", s3_dir_path)
        return listing




    @staticmethod
    def upload(bucket, path, file):
        """uploades file to cloud store"""
        s3_loc = S3Interface.build_s3_loc(bucket, path)
        upload_cmd = ["aws", "s3", "cp", file, s3_loc]
        upload_result = subprocess.run(upload_cmd, \
            check=False, capture_output=True, text=True)
        if upload_result.returncode != 0:
            logging.error("upload to %s failed with %s", s3_loc, upload_result.stderr)
            return {'success': False}
        return {'success': True}


    @staticmethod
    def download(s3_url, local_file):
        """downloads a file from cloud store"""
        download_cmd = ["aws", "s3", "cp", s3_url, local_file]
        download_result = subprocess.run(download_cmd, \
            check=False, capture_output=True, text=True)
        if download_result.returncode != 0:
            logging.error("download of %s failed with %s", s3_url, download_result.stderr)
            return {'success': False}
        return {'success': True}

    @staticmethod
    def remove(bucket, path):
        """removes file to cloud store"""
        s3_loc = S3Interface.build_s3_loc(bucket, path)
        remove_cmd = ["aws", "s3", "rm", s3_loc]
        remove_result = subprocess.run(remove_cmd, \
            check=False, capture_output=True, text=True)
        if remove_result.returncode != 0:
            logging.error("upload to %s failed with %s", s3_loc, remove_result.stderr)
            return {'success': False}
        return {'success': True}

    @staticmethod
    def compress(file):
        """compresses a local file"""
        compress_cmd = ["zstd", file]
        compress_result = subprocess.run(compress_cmd, \
            check=False, capture_output=True, text=True)
        if compress_result.returncode != 0:
            logging.error("compressing %s failed with %s", file, compress_result.stderr)
            return {'success': False, 'file': None}
        return {'success': True, 'file': file + '.zst'}

class Nodeos:
    """commands for working with nodeos"""
    @staticmethod
    def start_sync(data_dir, config_dir, stop_block_height, from_genesis=False):
        """start nodeos command"""
        # build command
        start_sync_cmd = ['nodeos', '--data-dir', data_dir + "/data", \
            '--config', config_dir + "/sync-config.ini", \
            '--terminate-at-block', stop_block_height ]
        # if start from genesis download genesis json and update cmd
        if from_genesis:
            genesis_file = data_dir + "/data/genesis.json"
            status = S3Interface.download(genesis_file, Genesis.cloud_url())
            if not status['success']:
                sys.exit("unable to download genesis file exiting")
            start_sync_cmd += [ '--genesis-json', genesis_file ]
        # run command this could run for some time
        start_sync_results = subprocess.run(start_sync_cmd, \
            check=False, capture_output=True, text=True)
        # error check
        if start_sync_results.returncode != 0:
            logging.error("nodeos start sync failed with %s", start_sync_results.stderr)
            sys.exit("nodes start sync failed with %s", start_sync_results.stderr)
        return {'success': True}

    @staticmethod
    def start_readonly(data_dir, config_dir):
        """start nodeos in readonly mode"""
        # build command
        start_ro_cmd = ['nodeos', '--data-dir', data_dir + "/data", \
            '--config', config_dir + "/readonly-config.ini"]
        # run command in background
        ro_process = subprocess.Popen(start_ro_cmd,
            bufsize=1024,
            close_fds=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)

        # return handle to process
        return ro_process

    @staticmethod
    def stop_readonly(process):
        """stop nodeos in readonly mode"""
        process.terminate()
        if process.returncode is None:
            logging.error("unable to terminate ro nodoes")
            sys.exit("unable to terminate read only nodeos")
        return {'success': True}

    @staticmethod
    def snapshot(base_url):
        """create a snapshot"""

        # "head_block_id": "string",
        # "head_block_num": 5102,
        # "head_block_time": "2020-11-16T00:00:00.000",
        # "version": 6,
        # "snapshot_name": "/home/me/nodes/node-name/snapshots/snapshot-sha.bin"

        get_headers = {
            'Accept': 'application/json',
        }
        params = {}
        job_response = requests.get(base_url + '/v1/producer/create_snapshot',
            params=params,
            headers=get_headers,
            timeout=150)

        if job_response.status_code != 200:
            logging.error("Error create_snapshot http call failed with status %s",
                job_response.status_code )
            sys.exit("Exiting create_snapshot http call failed with status %s",
                job_response.status_code)

        response_obj = json.loads(job_response.content.decode('utf-8'))
        logging.debug("created snapshot at %s for block num %s and head block time %s ",
            response_obj['snapshot_name'],
            response_obj['head_block_num'],
            response_obj['head_block_time'])
        return response_obj

    @staticmethod
    def get_integrity_hash(base_url):
        """get current integrity hash"""

        get_headers = {
            'Accept': 'application/json',
        }
        params = {}
        job_response = requests.get(base_url + '/v1/producer/get_integrity_hash',
            params=params,
            headers=get_headers,
            timeout=150)
        if job_response.status_code != 200:
            logging.error("Error get_integrity_hash http call failed with status %s",
                job_response.status_code )
            sys.exit("Exiting get_integrity_hash http call failed with status %s",
                job_response.status_code)

        response_obj = json.loads(job_response.content.decode('utf-8'))
        logging.debug("for block num %s got intrity hash %s ",
            response_obj['head_block_num'],
            response_obj['integrity_hash'])
        return response_obj


    @staticmethod
    def get_block_state(base_url):
        """return head block num and date"""
        # return json with following and possibly more
        # last_irreversible_block_num:347670570
        # last_irreversible_block_time:2023-12-19T22:55:53.500
        # head_block_num
        # head_block_time
        get_headers = {
            'Accept': 'application/json',
        }
        params = {}
        job_response = requests.get(base_url + '/v1/chain/get_info',
            params=params,
            headers=get_headers,
            timeout=15)

        if job_response.status_code != 200:
            logging.error("Error get_info http call failed with status %s",
                job_response.status_code )
            sys.exit("Exiting get_info http call failed with status %s",
                job_response.status_code)

        response_obj = json.loads(job_response.content.decode('utf-8'))
        head_block_num = response_obj['head_block_num']
        head_block_time = response_obj['head_block_time']
        last_irr_block_num = response_obj['last_irreversible_block_num']
        last_irr_block_time = response_obj['last_irreversible_block_time']

        if not head_block_num or not head_block_time:
            logging.error("Error get_info provided no value for head block num or block time")
            sys.exit("Error get_info provided no value for head block num or block time ")
        return {
            'head_block_num': head_block_num,
            'head_block_time': head_block_time,
            'last_irreversible_block_num': last_irr_block_num,
            'last_irreversible_block_time': last_irr_block_time
            }

    @staticmethod
    def build_snapshot_name(block_info):
        """create the snapshot name"""
        date_string = block_info['head_block_time']
        block_height = block_info['head_block_num']
        version = block_info['version']
        date_string = sub("T","-",date_string.split(':')[0])
        # example: snapshot-2018-06-17-16-eos-v6-0001214428.bin
        return f"snapshot-{date_string}-eos-v{version}-{block_height}.bin"

class Genesis:
    """return URL for Genesis json file"""
    @staticmethod
    def cloud_url():
        """convience func to return url to file"""
        return f"s3://{CLOUD_STORE}/{CLOUD_SOURCE_TYPE}/{CLOUD_SOURCE_TYPE}-genesis.json"

class Manifest:
    """opens manifest file with three columns
    start, end, span
    parses and expands manifest if start and end range contain spans"""
    def __init__(self, file):
        self.manifest = self.parse(file)
        self.manifest = self.expand()
        self.length = len(self.manifest)
        self.slice_instructions = self.ten_slices()

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
                    logging.debug("creating new record start %s end %s span %s",
                        inner_start, inner_end, span)
                    new_entries[inner_start]\
                        = {'start_num': inner_start, 'end_num':inner_end, 'span': span }
                    # start a new inner range
                    inner_start = int(inner_end)
        # loop over new entries and either add new records,
        # OR overwrite existing records
        # everything else is left the same
        if new_entries:
            for key, new_rec in new_entries.items():
                self.manifest[key] = new_rec
        # sort becuase new entries not added in key order
        return {k: self.manifest[k] for k in sorted(self.manifest)}

    def ten_slices(self):
        """divide into ten slices, for parallized run,
        overlapping block ranges to ensure continuity"""
        total_records = len(self.manifest)
        slice_size = numpy.floor_divide(total_records, 10)

        counter = slice_size
        slice_num = 1
        block_num_start = 0
        block_num_end = 0
        last_key = 0
        instructions = []

        for key in self.manifest.keys():
            last_key = key
            counter -= 1
            # last loop may have a few more rows
            # so we exclude the last slice and handle it
            # after the loop finishes
            if counter <= 0 and slice_num < 9:
                counter = slice_size
                logging.debug("ten_slices starting slice %s", slice_num)
                # end at next 2mil block span with overlap
                block_num_end = round(key/2000000)*2000000
                instructions.append({
                    'slice': slice_num,
                    'block_start': block_num_start,
                    'block_end': block_num_end-1,
                    'manifest_largest_start_num': key
                })
                # build the next slice
                slice_num += 1
                # start next at 2mil block span with overlap
                block_num_start = numpy.floor_divide(key,2000000)*2000000
        # do slice #10
        block_num_end = round(last_key/2000000)*2000000
        instructions.append({
            'slice': slice_num+1,
            'block_start': block_num_start,
            'block_end': block_num_end-1,
            'manifest_largest_start_num': last_key
        })
        return instructions

    def print_instructions(self):
        """Print out what snapshots to load to prep the slices,
        and what block number to terminate the slice"""
        logging.debug("instructions has %s entries", len(self.slice_instructions))

        # name only s3 listing
        snapshot_list = S3Interface.list(CLOUD_STORE, CLOUD_SOURCE_TYPE + "/snapshots/", True)
        snapshot_dict = {}
        # create a sorted dictionary of the snapshots
        for file in snapshot_list:
            block_num = int(file.split('-')[7].split('.')[0])
            snapshot_dict[block_num] = file
        snapshot_dict = {k: snapshot_dict[k] for k in sorted(snapshot_dict)}


        for record in self.slice_instructions:

            # find right snapshot from our list
            preceding_block_num = 0
            snapshot = "NA"
            for block_num in snapshot_dict.keys():
                if block_num >= record['block_start']:
                    break
                preceding_block_num = block_num

            if preceding_block_num == 0:
                snapshot = "genesis"
            else:
                snapshot = snapshot_dict[preceding_block_num]

            print(f"""
            ------ Slice {record['slice']} ------
            Load Snapshot {snapshot}
            Before Run Sync Until {record['block_start']}
            Normal sync will end at {record['manifest_largest_start_num']}
            **NOTE** continue syncing until {record['block_end']} to ensure overlap in block space

            """)

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
                logging.error("failed to find record matching %s", record['end_num'])
                return False
        return True

    def len(self):
        """return num of entries"""
        return self.length

    def __str__(self):
        return_str = ""
        for record in self.manifest.values():
            return_str += f"{record['start_num']}\t{record['end_num']}\t{record['span']}\n"
        return return_str

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='python script to run a full sync and drop \
snapshots at optimized block spacing based on a file')
    parser.add_argument('--debug', action=argparse.BooleanOptionalAction, \
        default=False, help='print debug stmts to stderr')
    parser.add_argument('--file', type=str,
        help='manifest of block ranges to take a snapshot')
    parser.add_argument('--instructions', action=argparse.BooleanOptionalAction, \
        default=False, help='instructions on how to setup slices')

    args = parser.parse_args()
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.ERROR)

    manifest = Manifest(args.file)
    if not manifest.is_valid:
        sys.exit("Manifest is_valid check failed")

    if args.instructions:
        logging.debug("printing instructions")
        manifest.print_instructions()
    else:
        logging.debug("NOT printing instructions")
        # else
        # loop over manifest start up nodoes to sync to end block
        # restart read only, take a snapshot give it a good named
        # restart sync mode to new block range
        # in the back ground blocks logs strided out
