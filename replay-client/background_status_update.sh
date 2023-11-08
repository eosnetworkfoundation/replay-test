#!/usr/bin/env bash

# runs in the background and updates the status of the snapshot loading and sync run

ORCH_IP=$1
ORCH_PORT=${2}
JOBID=$3
NODEOS_DIR=${4:-/data/nodeos}
STATUS="LOADING_SNAPSHOT"
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

loop_count=0

while [ $loop_count -lt 200 ]
do
  let "loop_count++"
  sleep 180
  # check for snapshot load complete
  if [ "$STATUS" == "LOADING_SNAPSHOT" ]; then
    # look for starting integrity hashes
    HASH=$("${SCRIPT_DIR}"/get_integrity_hash_from_log.sh "started" "$NODEOS_DIR")
    HASH_SIZE=$(echo $HASH | wc -c)
    # update status
    if [ $HASH_SIZE -gt 63 ]; then
      STATUS="WORKING"
      python3 "${SCRIPT_DIR}"/job_operations.py --host ${ORCH_IP} --port ${ORCH_PORT} \
         --operation update-status --status "${STATUS}" --job-id ${JOBID}
    fi
  else
    BLOCK_NUM=$("${SCRIPT_DIR}"/head_block_num_from_log.sh "$NODEOS_DIR")
    python3 "${SCRIPT_DIR}"/job_operations.py --host ${ORCH_IP} --port ${ORCH_PORT} \
        --operation update-progress --block-processed "$BLOCK_NUM" --job-id ${JOBID}
  fi
done
