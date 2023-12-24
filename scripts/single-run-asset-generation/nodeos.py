"""commands for working with nodeos"""
import logging
import sys
import json
import subprocess
from re import sub
import requests
from s3Interface import S3Interface
from genesis import Genesis

class Nodeos:
    """commands for working with nodeos"""
    @staticmethod
    def start_sync(data_dir, config_dir, stop_block_height,
        store=None, store_type=None, from_genesis=False):
        """start nodeos command"""
        # build command
        start_sync_cmd = ['nodeos', '--data-dir', data_dir + "/data", \
            '--config', config_dir + "/sync-config.ini", \
            '--terminate-at-block', stop_block_height ]
        # if start from genesis download genesis json and update cmd
        if from_genesis:
            genesis_file = data_dir + "/data/genesis.json"
            status = S3Interface.download(genesis_file,
                Genesis.cloud_url(store, store_type))
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
        ro_process = subprocess.Popen(start_ro_cmd)

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
