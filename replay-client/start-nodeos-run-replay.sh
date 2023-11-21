#!/usr/bin/env bash

#
# This script runs a replay job, updating status on orchestration service
# 1) performs file setup: create dirs, get snapshot to load
# 2) http GET job details from orchestration service, incls. block range
# 3) local non-priv install of nodeos
# 4) starts nodeos loads the snapshot
# 5) replay transactions to specified block height from blocks.log or networked peers and terminates
# 6) restart nodeos read-only mode to get final integrity hash
# 7) http POST completed status for configured block range
# 8) retain blocks logs copy over to cloud storage
# Communicates to orchestration service via HTTP
# Dependency on aws client, python3, curl, and large volume under /data
#
# Final status report available via HTTP showing all good
#    OR
# Final status shows block ranges with mismatched integrity hashes
#
# Author: Eric Passmore
# Date: Nov 6th 2023

ORCH_IP="${1:-127.0.0.1}"
ORCH_PORT="${2:-4000}"

REPLAY_CLIENT_DIR=/home/enf-replay/replay-test/replay-client
CONFIG_DIR=/home/enf-replay/replay-test/config
NODEOS_DIR=/data/nodeos

function trap_exit() {
  if [ -n "${BACKGROUND_STATUS_PID}" ]; then
    kill "${BACKGROUND_STATUS_PID}"
  fi
  if [ -n "${BACKGROUND_NODEOS_PID}" ]; then
    kill "${BACKGROUND_NODEOS_PID}"
  fi
  if [ -n "${JOBID}" ]; then
    python3 ${REPLAY_CLIENT_DIR}/job_operations.py --host ${ORCH_IP} --port ${ORCH_PORT} --operation update-status --status "ERROR" --job-id ${JOBID}
  fi
  echo "Caught signal exiting"
  exit 127
}

## set status to error if we exit on signal ##
trap trap_exit INT
trap trap_exit TERM

##################
# 1) performs file setup: create dirs, get snapshot to load
#################
## who we are ##
USER=enf-replay
TUID=$(id -ur)

## must not be root to run ##
if [ "$TUID" -eq 0 ]; then
  echo "Trying to run as root user exiting"
  exit
fi

## cleanup previous runs ##
"${REPLAY_CLIENT_DIR:?}"/replay-node-cleanup.sh "$USER"

## data volume must be large enough ##
volsize=$(df -h /data | awk 'NR==2 {print $4}' | sed 's/G//' | cut -d. -f1)
if [ ${volsize:-0} -lt 40 ]; then
  echo "/data volume does not exist or does not have 40Gb free space"
  exit 127
fi

## directory setup ##
"${REPLAY_CLIENT_DIR:?}"/create-nodeos-dir-struct.sh "${CONFIG_DIR}"

#################
# 2) http GET job details from orchestration service, incls. block range
#################
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

#################
# 3) local non-priv install of nodeos
#################
"${REPLAY_CLIENT_DIR:?}"/install-nodeos.sh $LEAP_VERSION
PATH=${PATH}:${HOME}/nodeos/usr/bin
export PATH

## copy snapshot ##
if [ $STORAGE_TYPE = "s3" ]; then
  echo "Copying snapshot to localhost"
  aws s3 cp "${SNAPSHOT_PATH}" "${NODEOS_DIR}"/snapshot/snapshot.bin.zst
else
  python3 "${REPLAY_CLIENT_DIR:?}"/job_operations.py --host ${ORCH_IP} --port ${ORCH_PORT} \
        --operation update-status --status "ERROR" --job-id ${JOBID}
  echo "Unknown snapshot type ${STORAGE_TYPE}"
  exit 127
fi
# restore blocks.log from cloud storage
echo "Restoring Blocks.log from Cloud Storage"
"${REPLAY_CLIENT_DIR:?}"/manage_blocks_log.sh "$NODEOS_DIR" "restore" $START_BLOCK $END_BLOCK "${SNAPSHOT_PATH}"

echo "Unzip snapshot"
zstd --decompress "${NODEOS_DIR}"/snapshot/snapshot.bin.zst

## update status that snapshot is loading ##
echo "Job status updated to LOADING_SNAPSHOT"
python3 ${REPLAY_CLIENT_DIR}/job_operations.py --host ${ORCH_IP} --port ${ORCH_PORT} \
        --operation update-status --status "LOADING_SNAPSHOT" --job-id ${JOBID}

#################
# 4) starts nodeos loads the snapshot, syncs to end block, and terminates
#################
echo "Start nodeos and sync till ${END_BLOCK}"

## update status when snapshot is complete: updates last block processed ##
## Background process grep logs on fixed interval secs ##
${REPLAY_CLIENT_DIR}/background_status_update.sh $ORCH_IP $ORCH_PORT $JOBID "$NODEOS_DIR" &
BACKGROUND_STATUS_PID=$!

sleep 5
nodeos \
     --snapshot "${NODEOS_DIR}"/snapshot/snapshot.bin \
     --data-dir "${NODEOS_DIR}"/data/ \
     --config "${CONFIG_DIR}"/sync-config.ini \
     --terminate-at-block ${END_BLOCK} \
     --integrity-hash-on-start \
     &> "${NODEOS_DIR}"/log/nodeos.log

kill $BACKGROUND_STATUS_PID
sleep 30

#################
# 5) get replay details from logs
#################
echo "Reached End Block ${END_BLOCK}, getting nodeos state details "
END_TIME=$(date '+%Y-%m-%dT%H:%M:%S')
START_BLOCK_ACTUAL_INTEGRITY_HASH=$("${REPLAY_CLIENT_DIR:?}"/get_integrity_hash_from_log.sh "started" "$NODEOS_DIR")

#################
# 6) restart nodeos read-only mode to get final integrity hash
#################
nodeos \
     --data-dir "${NODEOS_DIR}"/data/ \
     --config "${CONFIG_DIR}"/readonly-config.ini \
     &> "${NODEOS_DIR}"/log/nodeos-readonly.log &
BACKGROUND_NODEOS_PID=$!
sleep 30

END_BLOCK_ACTUAL_INTEGRITY_HASH=$(curl -s http://127.0.0.1:8888/v1/producer/get_integrity_hash | python3 ${REPLAY_CLIENT_DIR}/parse_json.py "integrity_hash")
# write hash to file, file not needed, backup for safety
echo "$END_BLOCK_ACTUAL_INTEGRITY_HASH" > "$NODEOS_DIR"/log/end_integrity_hash.txt

##
# we don't always know the integrity hash from the snapshot
# for example moving to a new version of leap, or upgrade to state db
# this updates the config and write out to a meta-data file on the server side
# POST back to config with expected integrity hash
python3 "${REPLAY_CLIENT_DIR:?}"/config_operations.py --host ${ORCH_IP} --port ${ORCH_PORT} \
   --end-block-num "$START_BLOCK" --integrity-hash "$START_BLOCK_ACTUAL_INTEGRITY_HASH"

# terminate read only nodeos in background
kill $BACKGROUND_NODEOS_PID

#################
# 7) http POST completed status for configured block range
#################
echo "Sending COMPLETE status"
python3 "${REPLAY_CLIENT_DIR:?}"/job_operations.py --host ${ORCH_IP} --port ${ORCH_PORT} \
    --operation complete --job-id ${JOBID} \
    --block-processed ${END_BLOCK} \
    --end-time "${END_TIME}" \
    --integrity-hash "${END_BLOCK_ACTUAL_INTEGRITY_HASH}"

#################
# 8) retain block log copy over to cloud storage
# retain - copies from local host to cloud storage
#################
"${REPLAY_CLIENT_DIR:?}"/manage_blocks_log.sh "$NODEOS_DIR" "retain" $START_BLOCK $END_BLOCK "${SNAPSHOT_PATH}"
