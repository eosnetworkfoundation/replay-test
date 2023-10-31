#!/usr/bin/env bash

ORCH_IP=ec2-52-91-58-149.compute-1.amazonaws.com
ORCH_PORT=4000

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
REPLAY_CLIENT_DIR=${SCRIPT_DIR}/replay-test/replay-client

## packages ##
sudo apt update >> /dev/null
sudo apt install -y git unzip jq curl python3

## aws cli ##
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# create enf-user
sudo ${REPLAY_CLIENT_DIR}/adduser.sh \
   "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIPbQbXU9uyqGwpeZxjeGR3Yqw8ku5iBxaKqzZgqHhphS support@eosnetwork.com - ANY"

# get the scripts
git clone https://github.com/eosnetworkfoundation/replay-test

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

# install the versions of nodeos we might need
${REPLAY_CLIENT_DIR}/install-nodeos.sh "${LEAP_VERSION}"
# setup directorys
sudo -u enf-replay ${REPLAY_CLIENT_DIR}/create-nodeos-dir-struct.sh ${SCRIPT_DIR}/config/config.ini

python3 ${REPLAY_CLIENT_DIR}/job_operations.py --host ${ORCH_IP} --port ${ORCH_PORT} --operation update-status --status "WORKING" --jobid ${JOBID}
sudo -u enf-replay ${SCRIPT_DIR}/start-nodeos.sh "${STORAGE_TYPE}" "${SNAPSHOT_PATH}" "${END_BLOCK}"
python3 ${REPLAY_CLIENT_DIR}/job_operations.py --host ${ORCH_IP} --port ${ORCH_PORT} --operation update-status --status "FINISHED" --jobid ${JOBID}
