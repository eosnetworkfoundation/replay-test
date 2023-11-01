#!/usr/bin/env bash

JOBID="${1}"
STORAGE_TYPE="${2}"
SNAPSHOT_PATH="${3}"
REPLAY_SLICE_ID="${4}"
START_BLOCK="${5}"
END_BLOCK="${6}"
EXPECTED_INTEGRITY_HASH="${7}"
ORCH_IP="${8:-127.0.0.1}"
ORCH_IP="${9:-4000}"

REPLAY_CLIENT_DIR=/home/enf-replay/replay-test/replay-client

function trap_exit() {
  if [ -n "${JOBID}" ]; then
    python3 ${REPLAY_CLIENT_DIR}/job_operations.py --host ${ORCH_IP} --port ${ORCH_PORT} --operation update-status --status "ERROR" --job-id ${JOBID}
  fi
  echo "caught signal exiting"
  exit 127
}

## set status to error if we exit ##
trap trap_exit EXIT

## who we are ##
USER=enf-replay
TUID=$(id -ur)

## must not be root to run ##
if [ "$TUID" -eq 0 ]; then
  echo "Trying to run as root user exiting"
  exit
fi

## copy snapshot ##
if [ $STORAGE_TYPE = "s3" ]; then
  aws s3 cp "${SNAPSHOT_PATH}" /home/enf-replay/snapshot/snapshot.bin.zst
else
  python3 ${REPLAY_CLIENT_DIR}/job_operations.py --host ${ORCH_IP} --port ${ORCH_PORT} --operation update-status --status "ERROR" --job-id ${JOBID}
  echo "unknown snapshot type ${STORAGE_TYPE}"
  exit 127
fi

python3 ${REPLAY_CLIENT_DIR}/job_operations.py --host ${ORCH_IP} --port ${ORCH_PORT} --operation update-status --status "WORKING" --job-id ${JOBID}

zstd --decompress /home/enf-replay/snapshot/snapshot.bin.zst

nodeos \
   --config-dir /home/"${USER}"/config/ \
   --data-dir /home/"$USER"/data/ \
   --snapshot /home/enf-replay/snapshot/snapshot.bin.zst \
   --truncate-at-block ${END_BLOCK} &> /home/"${USER}"/log/nodeos.log &

python3 ${REPLAY_CLIENT_DIR}/job_operations.py --host ${ORCH_IP} --port ${ORCH_PORT} --operation update-status --status "FINISHED" --job-id ${JOBID}
