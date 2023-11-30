"""Creates a manifest file from a list of snapshots sourced from an web page"""
import json
import re
import sys
import subprocess
import argparse
import requests
from bs4 import BeautifulSoup

# 1 - Connect to web page and parse out list of snapshots
# 2 - process list and create data structure, snapshot_manifest
# python3.10 generate_manifest_from_eosnation.py --source-net mainnet --leap-version 5.0.0-rc2

class ParseSnapshots:
    """Parse HTML page with list of snapshots"""
    def __init__(self, url, header_title):
        self.url = url
        self.header_title = header_title

    def get_content(self):
        """wrapper function to parse HTML and return snapshots as a list"""
        return self.get_snapshot_urls(self.get_card_content())

    def get_card_content(self):
        """parses cards and finds the returns HTML body"""
        # Make a GET request to the URL
        response = requests.get(self.url, timeout=3)
        if response.status_code != 200:
            print("Failed to fetch the URL", file=sys.stderr)
            sys.exit(1)

        # Parse the HTML content
        soup = BeautifulSoup(response.content, 'html.parser')

        # Find all divs with class "card-header-title"
        all_cards = soup.find_all("div", class_="card")
        for card in all_cards:
            # Find the 'header' element with class 'card-header'
            # that contains a 'p' element with class 'card-header-title'
            card_header = card.find("header", class_="card-header")
            if card_header:
                card_title = card_header.find("p", class_="card-header-title")
                if card_title and self.header_title in card_title.get_text().strip():
                    card_content = card_header.find_next_sibling("div", class_="card-content")
                    if card_content:
                        return card_content
        return None

    def get_snapshot_urls(self, card_content):
        """given an html list parse it and return the URLs"""
        url_list = []
        if card_content is None:
            return url_list

        snapshot_list = card_content.find_all("li")
        if snapshot_list:
            for element in snapshot_list:
                a_tag = element.find("a")
                if a_tag:
                    url = a_tag.get("href")
                    if url:
                        url_list.append(url)

        # add one fake snapshot for genesis
        url_list.append("https://ops.store.eosnation.io/eos-snapshots/snapshot-2018-06-10-01-eos-v6-0000000000.bin.zst") # pylint: disable=line-too-long
        return url_list

class Manifest:
    """Builds manifest and prints json config from list of snapshots"""
    def __init__(self, snapshots, source_net, leap_verison):
        self.snapshots = snapshots
        self.source_net = source_net
        self.leap_version = leap_verison
        self.block_heights = []
        self.manifest = []
        self.build()

    # needed my own integer check function
    # `isinstance` was too strict
    # pylint prefered `isinstance` over `type` check
    def is_integer(self, string):
        """custom check if is int"""
        if string is None:
            return False

        if isinstance(string, int):
            return True

        # Define a regex pattern for a positive integer
        pattern = r'^\d+$'
        match = re.match(pattern, string)

        return match is not None

    def url_to_s3_path(self, url):
        """convert URL to our S3 Path"""
        file_parts = url.split('/')
        if len(file_parts) >= 1:
            return f"s3://chicken-dance/{self.source_net}/snapshots/{file_parts[-1]}"

        return None

    def build(self):
        """constructs the manifest"""

        for url in self.snapshots:
            record = {
                'start_block_id': None,
                'end_block_id': None,
                'snapshot_path': None,
                'storage_type': 's3',
                'expected_integrity_hash': '',
                'leap_version': self.leap_version
            }
            # Split the string by either '-' or '.'
            parts = re.split(r'[-.]', url)
            # 3rd to last is the start block
            if len(parts) >= 3:
                if self.is_integer(parts[-3]):
                    start_block_num = int(parts[-3])
                    record['start_block_id'] = start_block_num
                    # list of block heights will use this to calc end_block_id
                    self.block_heights.append(start_block_num)

            s3_snapshot_path = self.url_to_s3_path(url)
            if s3_snapshot_path:
                record['snapshot_path'] = s3_snapshot_path

            self.manifest.append(record)

        # sort array desending
        self.block_heights.sort()

        # second pass to calculate end blocks
        for record in self.manifest:
            index = 0
            number_of_records = len(self.block_heights)

            # block_heights is a sorted array.
            # when the block height matches the start_block_id
            # the very next element in block_heights is the end_block_id
            # wrap with check to make sure index is not out of bounds
            while index < number_of_records:
                if self.block_heights[index] == record['start_block_id']:
                    if index + 1 < number_of_records:
                        record['end_block_id'] = self.block_heights[index+1]
                    # found match end this while loop
                    break
                index += 1

        # remove all items that are not valid, typically very first and last
        self.manifest = [rc for rc in self.manifest \
          if (rc['start_block_id'] or rc['start_block_id'] == 0) \
          and rc['end_block_id'] and rc['snapshot_path'] \
          and rc['start_block_id'] < rc['end_block_id']]

        # lastly clean up
        self.clean_snapshot_list()

    def __str__(self):
        return json.dumps(self.manifest, indent=4)

    def clean_snapshot_list(self):
        """iterate through URL snapshot and rm entries that are not in manifest"""

        # if manifest does not exist no need to run exit early
        if len(self.manifest) == 0:
            return

        # iterate over snapshots
        # at end delete records with no matches
        index = 0
        number_of_snapshots = len(self.snapshots)
        while index < number_of_snapshots:
            has_match = False
            url_file_parts = self.snapshots[index].split('/')
            if len(url_file_parts) >= 1:
                snapshot_file = url_file_parts[-1]
            # iterate over known good manifest list
            for record in self.manifest:
                record_file_parts = record['snapshot_path'].split('/')
                if len(record_file_parts) >= 1:
                    # match we are done searching
                    # set flag and exit loop
                    if snapshot_file == record_file_parts[-1]:
                        has_match = True
                        break
            if not has_match:
                number_of_snapshots -= 1
                del self.snapshots[index]

            index += 1

    def upload_snapshots(self):
        """upload snapshots to cloud storage"""
        for url in self.snapshots:
            s3_snapshot_path = self.url_to_s3_path(url)
            if s3_snapshot_path:
                # test does file exist already
                s3_parts = s3_snapshot_path.split('/')
                if len(s3_parts) > 3:
                    bucket  = s3_parts[2]
                    s3_path = '/'.join(s3_parts[3:])
                    download_file = "/tmp/snapshot.bin.zst"
                    # build commands
                    s3_file_exists = ["aws", "s3api", "head-object", \
                        "--bucket", bucket, "--key", s3_path]
                    download_cmd = ["curl", "-s", "-o", download_file, url]
                    upload_cmd = ["aws", "s3", "cp", download_file, s3_snapshot_path]
                    remove_cmd = ["rm", download_file]
                    # execute
                    exists_result = subprocess.run(s3_file_exists, \
                        check=False, capture_output=True, text=True)
                    if exists_result.returncode != 0:
                        # file does not exist proceed
                        print(f"{s3_path} does not exist in cloud store", file=sys.stderr)
                        download_result = subprocess.run(download_cmd, \
                            check=True, capture_output=True, text=True)
                        # check if download succeeded
                        if download_result.returncode != 0:
                            print(f"unable to download {url} {download_result.stderr}", file=sys.stderr)
                        else:
                            # now upload to cloud and remove from localhost
                            subprocess.run(upload_cmd, check=False)
                            subprocess.run(remove_cmd, check=False)
                            print(f"successfully uploaded {s3_path}", file=sys.stderr)
                    else:
                        print(f"file {s3_path} already exists nothing to upload", file=sys.stderr)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='helper script to build manifest that drives chicken dance')
    parser.add_argument('--source-net', type=str, default='mainnet',
        help='which chain to use e.g. mainnet or jungle')
    parser.add_argument('--snapshot-version', type=str, default='v6',
        help='version of snapshot, default v6')
    parser.add_argument('--leap-version', type=str, default='5.0.0',
        help='version of leap, default 5.0.0')
    parser.add_argument('--upload-snapshots', action=argparse.BooleanOptionalAction, \
        default=False, help='upload snapshot to cloud storage, warning this takes time')

    args = parser.parse_args()

    search_title = f"{args.source_net} - {args.snapshot_version}"
    if args.source_net.lower() == "mainnet":
        search_title = f"EOS Mainnet - {args.snapshot_version}"
    if "jungle" in args.source_net.lower():
        search_title = f"Jungle 4 Testnet - {args.snapshot_version}"
    if "kylin" in args.source_net.lower():
        search_title = f"Kylin Testnet - {args.snapshot_version}"

    parser = ParseSnapshots("https://snapshots.eosnation.io/", search_title)
    list_of_snapshots = parser.get_content()
    if not list_of_snapshots:
        print("Failed to match, no sources found", file=sys.stderr)
        sys.exit(1)

    # strip out whitespace to get name of chain
    CHAIN_NAME = ''.join(args.source_net.lower().split())
    manifest = Manifest(list_of_snapshots, CHAIN_NAME, args.leap_version.lower())
    if args.upload_snapshots:
        print("uploading snapshots: warning this can take time", file=sys.stderr)
        manifest.upload_snapshots()
    print(manifest)
