#!/usr/bin/env bash

ORCH_IP=127.0.0.1
ORCH_PORT=4000

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
REPLAY_CLIENT_DIR=${SCRIPT_DIR}/../replay-client

# update
apt update
# get the scripts
if [ -n "$BRANCH" ]; then
  git clone -b "$BRANCH" https://github.com/eosnetworkfoundation/replay-test
else
  git clone https://github.com/eosnetworkfoundation/replay-test
fi

## packages ##
apt update >> /dev/null
apt install unzip jq curl python3

## aws cli ##
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
./aws/install

python3 ${REPLAY_CLIENT_DIR}/job_operations.py --host ${ORCH_IP} --port ${ORCH_PORT} --operation pop > /tmp/job.conf.json

STATUS=$(cat /tmp/job.conf.json | python3 ${REPLAY_CLIENT_DIR}/parse_json.py "status_code")
if [ $STATUS -ne 200 ]; then
  echo "FAILED TO AQUITE JOB"
  exit 127
fi

JOBID=$(cat /tmp/job.conf.json | python3 ${REPLAY_CLIENT_DIR}/parse_json.py "job_id")
START_BLOCK=$(cat /tmp/job.conf.json | python3 ${REPLAY_CLIENT_DIR}/parse_json.py "start_block_num")
END_BLOCK=$(cat /tmp/job.conf.json | python3 ${REPLAY_CLIENT_DIR}/parse_json.py "end_block_num")
REPLAY_SLICE_ID=$(cat /tmp/job.conf.json | python3 ${REPLAY_CLIENT_DIR}/parse_json.py "replay_slice_id")
SNAPSHOT_PATH=$(cat /tmp/job.conf.json | python3 ${REPLAY_CLIENT_DIR}/parse_json.py "snapshot_path")
STORAGE_TYPE=$(cat /tmp/job.conf.json | python3 ${REPLAY_CLIENT_DIR}/parse_json.py "storage_type")
EXPECTED_INTEGRITY_HASH=$(cat /tmp/job.conf.json | python3 ${REPLAY_CLIENT_DIR}/parse_json.py "expected_integrity_hash")
LEAP_VERSION=$(cat /tmp/job.conf.json | python3 ${REPLAY_CLIENT_DIR}/parse_json.py "leap_version")

# setup user and install nodeos
sudo ${SCRIPT_DIR}/nodeos-setup.sh \
   "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIPbQbXU9uyqGwpeZxjeGR3Yqw8ku5iBxaKqzZgqHhphS support@eosnetwork.com - ANY"\
   ${LEAP_VERSION}

python3 ${REPLAY_CLIENT_DIR}/job_operations.py --host ${ORCH_IP} --port ${ORCH_PORT} --operation update-status --status "WORKING" --jobid ${JOBID}
${SCRIPT_DIR}/start-nodeos.sh "${STORAGE_TYPE}" "${SNAPSHOT_PATH}" "${END_BLOCK}"
python3 ${REPLAY_CLIENT_DIR}/job_operations.py --host ${ORCH_IP} --port ${ORCH_PORT} --operation update-status --status "FINISHED" --jobid ${JOBID}
