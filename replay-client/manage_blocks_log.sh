#!/usr/bin/env bash

# Pulls block log file from cloud storage or saves block log to cloud storage
# Params
#
# NODEOS_DIR - local host top level directory
# OPERATION - retain: copy to cloud OR restore: copy from cloud
# START_BLOCK_NUM - starting block to lable blocks log
# END_BLOCK_NUM - ending block to lable blocks log
# SNAPSHOT_PATH - used to figure out cloud directory and bucket
#


NODEOS_DIR=${1:-/data/nodeos}
OPERATION=$2
START_BLOCK_NUM=$3
END_BLOCK_NUM=$4
SNAPSHOT_PATH=${5:-s3://chicken-dance/default/snapshots/snapshot.bin.zst}

# validate params
if [ -z "$OPERATION" ] || [ -z "$START_BLOCK_NUM" ] || [ -z "$END_BLOCK_NUM" ]; then
  echo "Must provider operation, start block num and end block num to manage_block_log.sh"
  exit 127
fi

# lowercase operation
OPERATION=$(echo "$OPERATION" | tr '[:upper:]' '[:lower:]')

# Figure out S3 Blocks log dir from provided snapshot path
# Remove the last directory using dirname
S3_DIR="$(dirname "$SNAPSHOT_PATH")"
# Strip off the file and last directory
S3_DIR="${S3_DIR%/*}"/blocks
# figure out s3 bucket
S3_BUCKET=$(echo "${S3_DIR}" | sed 's#s3://##' | cut -d'/' -f1)
# figure out s3 path
S3_PATH=$(echo "${S3_DIR}" | sed 's#s3://##' | cut -d'/' -f2-)
# figure out file name
S3_FILE=blocks-${START_BLOCK_NUM}-${END_BLOCK_NUM}.log

# does S3 file exist
aws s3api head-object --bucket "$S3_BUCKET" --key "$S3_PATH"/"$S3_FILE" > /dev/null 2>&1 || NOT_EXIST=true

if [ "$OPERATION" == "retain" ]; then
  if [ $NOT_EXIST ]; then
    aws s3 cp "$NODEOS_DIR"/data/blocks/blocks.log "${S3_DIR}"/"$S3_FILE"
    # TODO: add uncompress step issue #31
  else
    echo "blocks.log file already exists, skipping backup to cloud storage"
  fi
elif [ "$OPERATION" == "restore" ]; then
  if [ $NOT_EXIST ]; then
    echo "${S3_DIR}/${S3_FILE} does not exist skipping blocks log restore step"
  else
    # TODO: add compression step issue #31
    aws s3 cp "${S3_DIR}"/"$S3_FILE" "$NODEOS_DIR"/data/blocks/blocks.log
    leap-util block-log --blocks-dir "$NODEOS_DIR"/data/blocks/ smoke-test > /dev/null 2>&1 || FAILED_SMOKE_TEST=true
    # try an obvious repair
    if [ $FAILED_SMOKE_TEST ]; then
      leap-util block-log --blocks-dir "$NODEOS_DIR"/data/blocks/ make-index >> "$NODEOS_DIR"/log/leap-util.log
      unset FAILED_SMOKE_TEST
    fi
    # retest
    leap-util block-log --blocks-dir "$NODEOS_DIR"/data/blocks/ smoke-test > /dev/null 2>&1 || FAILED_SMOKE_TEST=true
    if [ $FAILED_SMOKE_TEST ]; then
      echo "Smoke test for Blocks log ${NODEOS_DIR}/data/blocks/ failed exiting"
      exit 127
    fi
  fi
else
  echo "unknow operation ${OPERATION} provided to manage_block_log.sh"
  exit 127
fi
