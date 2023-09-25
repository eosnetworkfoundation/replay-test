#!/usr/bin/env bash

ORCH_IP=127.0.0.1
ORCH_PORT=4000

jitter () {
  # number between 1 and 5000
  random_ms=$(( $RANDOM % 5000 + 1 ))
  # scale 3 places right of decimal 0.000
  random_sec=$(echo "scale=3; ${random_ms}/1000" | bc)
  # return seconds between 0.001 and 5.000
  return "$random_sec"
}

backoff_pause () {
  last_backup=$1
  # scale 2 places right of decimal 0.00
  last_backup=$(echo "scale=2; ${last_backup} * 2" | bc)
  if [ "$last_backup" -gt 5 ]; then
    last_backup=5
  fi
  return $last_backup
}

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
apt install unzip jq curl

## aws cli ##
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
./aws/install

## get job config ##
# random wait congestion avoidance
sleep jitter
curl http://${ORCH_IP}:${ORCH_PORT}/job\?nextjob=1 -H "Accept: application/json" > /tmp/job.conf.json


# setup
sudo ./replay-test/scripts/nodeos-setup.sh "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIPbQbXU9uyqGwpeZxjeGR3Yqw8ku5iBxaKqzZgqHhphS support@eosnetwork.com - ANY"
