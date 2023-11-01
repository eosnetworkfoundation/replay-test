#!/usr/bin/env bash

ORCH_IP="${1}"
ORCH_PORT=4000

function trap_exit() {
  if [ -n "${JOBID}" ]; then
    python3 ${REPLAY_CLIENT_DIR}/job_operations.py --host ${ORCH_IP} --port ${ORCH_PORT} --operation update-status --status "ERROR" --job-id ${JOBID}
  fi
  echo "caught signal exiting"
  exit 127
}

## set status to error if we exit ##
trap trap_exit EXIT

## directories ##
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
REPLAY_CLIENT_DIR=${SCRIPT_DIR}/replay-test/replay-client

## packages ##
sudo apt update >> /dev/null
sudo apt install -y git unzip jq curl python3

## aws cli ##
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

## get the scripts ##
git clone https://github.com/eosnetworkfoundation/replay-test

## create enf-user ##
sudo ${REPLAY_CLIENT_DIR}/adduser.sh \
   "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIPbQbXU9uyqGwpeZxjeGR3Yqw8ku5iBxaKqzZgqHhphS support@eosnetwork.com - ANY"

## get the job ##
## need job details to get leap version
## leap deb install requires root
## once leap install is complete we switch to enf-user
python3 ${REPLAY_CLIENT_DIR}/job_operations.py --host ${ORCH_IP} --port ${ORCH_PORT} --operation pop > /tmp/job.conf.json

STATUS=$(cat /tmp/job.conf.json | python3 ${REPLAY_CLIENT_DIR}/parse_json.py "status_code")
if [ $STATUS -ne 200 ]; then
  echo "FAILED TO AQUITE JOB"
  exit 127
fi

## Parse from json ###
JOBID=$(cat /tmp/job.conf.json | python3 ${REPLAY_CLIENT_DIR}/parse_json.py "job_id")
START_BLOCK=$(cat /tmp/job.conf.json | python3 ${REPLAY_CLIENT_DIR}/parse_json.py "start_block_num")
END_BLOCK=$(cat /tmp/job.conf.json | python3 ${REPLAY_CLIENT_DIR}/parse_json.py "end_block_num")
REPLAY_SLICE_ID=$(cat /tmp/job.conf.json | python3 ${REPLAY_CLIENT_DIR}/parse_json.py "replay_slice_id")
SNAPSHOT_PATH=$(cat /tmp/job.conf.json | python3 ${REPLAY_CLIENT_DIR}/parse_json.py "snapshot_path")
STORAGE_TYPE=$(cat /tmp/job.conf.json | python3 ${REPLAY_CLIENT_DIR}/parse_json.py "storage_type")
EXPECTED_INTEGRITY_HASH=$(cat /tmp/job.conf.json | python3 ${REPLAY_CLIENT_DIR}/parse_json.py "expected_integrity_hash")
LEAP_VERSION=$(cat /tmp/job.conf.json | python3 ${REPLAY_CLIENT_DIR}/parse_json.py "leap_version")

## install the versions of nodeos we might need ##
sudo ${REPLAY_CLIENT_DIR}/install-nodeos.sh "${LEAP_VERSION}"

## install scripts to enf-replay users ##
sudo -u enf-replay sh -c 'cd /home/enf-replay && git clone https://github.com/eosnetworkfoundation/replay-test'
## setup directories for enf-user ##
sudo -u enf-replay /home/enf-replay/replay-test/replay-client/create-nodeos-dir-struct.sh /home/enf-replay/replay-test/config/config.ini

## all done with sudo access ##
## switch over to local user ##
## run replay , run nodeos as local user ##
sudo -u enf-replay /home/enf-replay/replay-test/replay-client/start-nodeos-run-replay.sh "${JOBID}" \
  "${STORAGE_TYPE}" \
  "${SNAPSHOT_PATH}" \
  "${REPLAY_SLICE_ID}" \
  "${START_BLOCK}" \
  "${END_BLOCK}" \
  "${EXPECTED_INTEGRITY_HASH}" \
  "${ORCH_IP}" \
  "${ORCH_PORT}"
