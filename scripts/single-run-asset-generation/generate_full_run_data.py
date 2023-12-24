"""Single node run over entire history with snapshot spaced at specified block heights"""
import sys
import argparse
import logging
import tomli
from manifest import Manifest

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

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='python script to run a full sync and drop \
snapshots at optimized block spacing based on a file')
    parser._action_groups.pop()
    required = parser.add_argument_group('required arguments')
    optional = parser.add_argument_group('optional arguments')
    required.add_argument('--file', type=str,
            help='manifest of block ranges to take a snapshot')
    optional.add_argument('--debug', action=argparse.BooleanOptionalAction, \
        default=False, help='print debug stmts to stderr')
    optional.add_argument('--instructions', action=argparse.BooleanOptionalAction, \
        default=False, help='instructions on how to setup slices')

    args = parser.parse_args()
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.ERROR)

    if not args.file:
        sys.exit("Must specific file see --help for more info")
    manifest = Manifest(args.file)
    if not manifest.is_valid:
        sys.exit("Manifest is_valid check failed")

    if args.instructions:
        logging.debug("printing instructions")
        manifest.print_instructions(CLOUD_STORE, CLOUD_SOURCE_TYPE)
    else:
        logging.debug("NOT printing instructions")
        print(manifest)
