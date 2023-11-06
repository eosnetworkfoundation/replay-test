#!/usr/bin/env bash

#
# This script runs a replay job, updating status on orchestration service
# 1) performs file setup: create dirs, get snapshot to load
# 2) pulls in job details from orchestration service
# 3) local non-priv install of nodeos
# 4) runs the replay
# Communicates to orchestration service via HTTP
# Dependancy on aws client, python3, curl, and large volume under /data
#
# Author: Eric Passmore
# Date: Nov 5th 2023

ORCH_IP="${1:-127.0.0.1}"
ORCH_PORT="${2:-4000}"

REPLAY_CLIENT_DIR=/home/enf-replay/replay-test/replay-client
CONFIG_DIR=/home/enf-replay/replay-test/config
NODEOS_DIR=/data/nodeos

function trap_exit() {
  if [ -n "${JOBID}" ]; then
    python3 ${REPLAY_CLIENT_DIR}/job_operations.py --host ${ORCH_IP} --port ${ORCH_PORT} --operation update-status --status "ERROR" --job-id ${JOBID}
  fi
  echo "Caught signal exiting"
  exit 127
}

## set status to error if we exit on signal ##
trap trap_exit INT
trap trap_exit TERM

## who we are ##
USER=enf-replay
TUID=$(id -ur)

## must not be root to run ##
if [ "$TUID" -eq 0 ]; then
  echo "Trying to run as root user exiting"
  exit
fi
## data volume must be large enough ##
volsize=$(df -h /data | awk 'NR==2 {print $4}' | sed 's/G//' | cut -d. -f1)
if [ ${volsize:-0} -lt 40 ]; then
  echo "/data volume does not exist or does not have 40Gb free space"
  exit 127
fi

## directory setup ##
"${REPLAY_CLIENT_DIR:?}"/create-nodeos-dir-struct.sh "${CONFIG_DIR}"

## get job details ##
## need job details to get leap version and copy snapshot
python3 "${REPLAY_CLIENT_DIR:?}"/job_operations.py --host ${ORCH_IP} --port ${ORCH_PORT} --operation pop > /tmp/job.conf.json

STATUS=$(cat /tmp/job.conf.json | python3 "${REPLAY_CLIENT_DIR:?}"/parse_json.py "status_code")
if [ $STATUS -ne 200 ]; then
  echo "Failed to aquire job"
  exit 127
fi
echo "Received job details processing..."

## Parse from json ###
JOBID=$(cat /tmp/job.conf.json | python3 ${REPLAY_CLIENT_DIR}/parse_json.py "job_id")
START_BLOCK=$(cat /tmp/job.conf.json | python3 ${REPLAY_CLIENT_DIR}/parse_json.py "start_block_num")
END_BLOCK=$(cat /tmp/job.conf.json | python3 ${REPLAY_CLIENT_DIR}/parse_json.py "end_block_num")
REPLAY_SLICE_ID=$(cat /tmp/job.conf.json | python3 ${REPLAY_CLIENT_DIR}/parse_json.py "replay_slice_id")
SNAPSHOT_PATH=$(cat /tmp/job.conf.json | python3 ${REPLAY_CLIENT_DIR}/parse_json.py "snapshot_path")
STORAGE_TYPE=$(cat /tmp/job.conf.json | python3 ${REPLAY_CLIENT_DIR}/parse_json.py "storage_type")
EXPECTED_INTEGRITY_HASH=$(cat /tmp/job.conf.json | python3 ${REPLAY_CLIENT_DIR}/parse_json.py "expected_integrity_hash")
LEAP_VERSION=$(cat /tmp/job.conf.json | python3 ${REPLAY_CLIENT_DIR}/parse_json.py "leap_version")

## setup nodeos ##
"${REPLAY_CLIENT_DIR:?}"/install-nodeos.sh $LEAP_VERSION
PATH=${PATH}:${HOME}/nodeos/usr/bin
export PATH

## copy snapshot ##
if [ $STORAGE_TYPE = "s3" ]; then
  echo "Copying snapshot to localhost"
  aws s3 cp "${SNAPSHOT_PATH}" "${NODEOS_DIR}"/snapshot/snapshot.bin.zst
else
  python3 "${REPLAY_CLIENT_DIR:?}"/job_operations.py --host ${ORCH_IP} --port ${ORCH_PORT} --operation update-status --status "ERROR" --job-id ${JOBID}
  echo "Unknown snapshot type ${STORAGE_TYPE}"
  exit 127
fi

echo "Job status updated to WORKING"
python3 "${REPLAY_CLIENT_DIR:?}"/job_operations.py --host ${ORCH_IP} --port ${ORCH_PORT} --operation update-status --status "WORKING" --job-id ${JOBID}

echo "Unzip snapshot"
zstd --decompress "${NODEOS_DIR}"/snapshot/snapshot.bin.zst

## load from snapshot ##
## sync till block ##
echo "Start nodeos and sync till ${END_BLOCK}"
nodeos \
     --snapshot "${NODEOS_DIR}"/snapshot/snapshot.bin \
     --data-dir "${NODEOS_DIR}"/data/ \
     --config "${CONFIG_DIR}"/sync-config.ini \
     --terminate-at-block ${END_BLOCK} \
     &> "${NODEOS_DIR}"/log/nodeos.log

## restart to get details ##
echo "Restart nodeos readonly mode"
nodeos \
     --data-dir "${NODEOS_DIR}"/data/ \
     --config "${CONFIG_DIR}"/readonly-config.ini \
     &>> "${NODEOS_DIR}"/log/nodeos.log &
NODEOS_PID=$!

## allow time for nodoes to start up ## 
sleep 30
echo "Getting integrity hash and head block num"
END_TIME=$(date '+%Y-%m-%dT%H:%M:%S')

ACTUAL_INTEGRITY_HASH=$(curl -s http://127.0.0.1:8888/v1/producer/get_integrity_hash | python3 ${REPLAY_CLIENT_DIR}/parse_json.py "integrity_hash")
GET_HASH_STATUS=$?

HEAD_BLOCK_NUM=$(curl -s http://127.0.0.1:8888/v1/chain/get_info | python3 ${REPLAY_CLIENT_DIR}/parse_json.py "head_block_num")
GET_BLOCK_STATUS=$?

if [ $GET_HASH_STATUS -ne 0 ] || [ $GET_BLOCK_STATUS -ne 0 ]; then
  python3 ${REPLAY_CLIENT_DIR}/job_operations.py --host ${ORCH_IP} --port ${ORCH_PORT} --operation update-status --status "ERROR" --job-id ${JOBID}
fi

## terminate nodeos we have what we need ##
echo "Terminating nodoes"
kill $NODEOS_PID

## complete status ##
echo "Sending COMPLETE status"
python3 "${REPLAY_CLIENT_DIR:?}"/job_operations.py --host ${ORCH_IP} --port ${ORCH_PORT} \
    --operation complete --job-id ${JOBID} \
    --block-processed $HEAD_BLOCK_NUM \
    --end-time "${END_TIME}" \
    --integrity-hash "${ACTUAL_INTEGRITY_HASH}"
