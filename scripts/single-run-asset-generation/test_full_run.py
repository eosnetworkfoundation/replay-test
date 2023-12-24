"""Test Single Run"""
import unittest
import os
import random
import logging
import time
from full_run import Manifest, S3Interface, Nodeos, Genesis

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
        self.assertTrue(test_manifest.is_valid())
        self.assertEqual(test_manifest.len(), 7)

class TestS3Interface(unittest.TestCase):
    """tests for S3 commands"""

    def test_path(self):
        """test s3 path"""
        full_path = S3Interface.build_s3_loc("chicken-dance", "test/dir/file.bin.zst")
        self.assertEqual(full_path,"s3://chicken-dance/test/dir/file.bin.zst")
        full_path_extra_slash = S3Interface.build_s3_loc("chicken-dance/",
            "test/dir/file.bin.zst")
        self.assertEqual(full_path_extra_slash, full_path)

    # compress smaller check
    def test_compress(self):
        """test compress"""
        original_file = "compress_file.txt"
        compress_file = "compress_file.txt.zst"

        # create large file
        with open(original_file, 'w', encoding='utf-8') as file:
            for _ in range(10000):
                one = random.randint(1, 999999999)
                two = random.randint(1, 999999999)
                three = random.randint(1, 999999999)
                file.write(f"{one}\t{two}\t{three}\n")

        pre_size = os.path.getsize(original_file)
        result = S3Interface.compress(original_file)
        self.assertTrue(result['success'])

        post_size = os.path.getsize(result['file'])
        self.assertTrue(pre_size > post_size)
        os.remove(original_file)
        os.remove(compress_file)

    # rm local ;download passes; local exists true
    def test_download(self):
        """test s3 download"""
        test_genesis = S3Interface.build_s3_loc("chicken-dance","test/test-genesis.json")
        local_file = "test_genesis.json"
        result = S3Interface.download(test_genesis, local_file)
        self.assertTrue(result['success'])
        dl_file_size = os.path.getsize(local_file)
        self.assertTrue(dl_file_size > 1)
        os.remove(local_file)

    def test_not_exists(self):
        """negative test case of exists"""
        self.assertTrue(not S3Interface.exists("chicken-dance","test/do_not_exist.txt"))

    def test_upload(self):
        """test upload, and exists, then upload, and remove"""
        bucket = "chicken-dance"
        # create sample file to upload
        hello_up_file = 'hello_world.txt'
        with open(hello_up_file, 'w', encoding='utf-8') as file:
            file.write("Hello World!\n")
        # make sure file does not exist already
        file_path = "test/" + hello_up_file
        self.assertTrue(not S3Interface.exists(bucket, file_path))
        # upload
        S3Interface.upload(bucket, file_path, hello_up_file)
        # file should exist
        self.assertTrue(S3Interface.exists(bucket, file_path))
        # remove
        S3Interface.remove(bucket, file_path)
        # no more file
        self.assertTrue(not S3Interface.exists(bucket, file_path))
        # rm local
        os.remove(hello_up_file)

class TestNodeos(unittest.TestCase):
    """Test for nodeos commands"""
    def test_sync(self):
        """Test running a sync and seeing head block move forward"""
        data_dir="/data/nodeos"
        config_dir="/home/enf-replay/config"
        stop_block_height = 30530359

        ro_process = Nodeos.start_readonly(data_dir, config_dir)
        block_info_before = Nodeos.get_block_state("http://127.0.0.1:8888")
        self.assertTrue(block_info_before['head_block_num'] > 30000000)
        self.assertTrue(block_info_before['head_block_num'] < 30530359)

        hash_info_before = Nodeos.get_integrity_hash("http://127.0.0.1:8888")
        self.assertTrue(len(hash_info_before['integrity_hash']) > 64)

        result = Nodeos.stop_readonly(ro_process)
        self.assertTrue(result['success'])

        result = Nodeos.start_sync(data_dir, config_dir, stop_block_height, from_genesis=False)
        self.assertTrue(result['success'])

        ro_process = Nodeos.start_readonly(data_dir, config_dir)
        block_info_after = Nodeos.get_block_state("http://127.0.0.1:8888")
        self.assertTrue(block_info_after['head_block_num'] > block_info_before['head_block_num'])

        hash_info_after = Nodeos.get_integrity_hash("http://127.0.0.1:8888")
        self.assertTrue(len(hash_info_after['integrity_hash']) > 64)
        self.assertTrue(hash_info_after['integrity_hash'] != hash_info_before['integrity_hash'])

        result = Nodeos.stop_readonly(ro_process)
        self.assertTrue(result['success'])

    def test_snapshot(self):
        """get a snapshot and integrity hash from readonly node"""
        data_dir="/data/nodeos"
        config_dir="/home/enf-replay/config"

        ro_process = Nodeos.start_readonly(data_dir, config_dir)
        logging.debug("sleeping after starting nodeos")
        time.sleep(30)
        logging.debug("sleep complete")

        snapshot_info = Nodeos.snapshot("http://127.0.0.1:8888")
        self.assertTrue(os.path.exists(snapshot_info['snapshot_name']))
        self.assertTrue(snapshot_info['head_block_num'] > 0)

        logging.debug("another quick sleep")
        time.sleep(3)
        result = Nodeos.stop_readonly(ro_process)
        self.assertTrue(result['success'])

    def test_snapshot_name(self):
        """test name func"""
        block_info = {
            "head_block_time": "2023-12-19T22:55:53.500",
            "head_block_num": "012344556",
            "version": 6
        }

        snapshot_name = Nodeos.build_snapshot_name(block_info)
        self.assertEqual(snapshot_name, "snapshot-2023-12-19-22-eos-v6-012344556.bin")


class TestGenesis(unittest.TestCase):
    """Test the genesis Name"""
    def test_name(self):
        """test cloud name for genesis"""
        url = Genesis.cloud_url()
        self.assertEqual(url, "s3://chicken-dance/mainnet/mainnet-genesis.json")


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()
