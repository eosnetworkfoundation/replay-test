"""Test Single Run"""
import unittest
import os
import random
import logging
import time
from s3Interface import S3Interface
from manifest import Manifest
from genesis import Genesis

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

class TestGenesis(unittest.TestCase):
    """Test the genesis Name"""
    def test_name(self):
        """test cloud name for genesis"""
        url = Genesis.cloud_url("chicken-dance","mainnet")
        self.assertEqual(url, "s3://chicken-dance/mainnet/mainnet-genesis.json")


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()
