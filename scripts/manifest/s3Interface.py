"""cli commands to interfaces with S3 storage"""
import subprocess
import logging

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
