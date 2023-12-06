#!/usr/bin/env bash

USER=ubuntu

## packages ##
apt-get update >> /dev/null
apt-get install -y git unzip jq curl python3 python3-pip

## aws cli ##
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "/tmp/awscliv2.zip"
unzip /tmp/awscliv2.zip -d /tmp/ >> /dev/null
/tmp/aws/install
rm -rf /tmp/aws /tmp/awscliv2.zip

## git scripts for enf-user ##
sudo -i -u "${USER}" git clone https://github.com/eosnetworkfoundation/replay-test
sudo -i -u "${USER}" pip install datetime argparse werkzeug bs4

## setup log rotate ##
cp /home/"${USER}"/replay-test/scripts/orchestration-logrotate.conf /etc/logrotate.d/replay-orchestration

## startup service in background ##
sudo -i -u "${USER}" python3 /home/"${USER}"/replay-test/orchestration-service/web_service.py \
    --config /home/"${USER}"/replay-test/meta-data/full-production-run-20231130.json \
    --host 0.0.0.0 \
    --log /home/"${USER}"/orch-complete-timings.log &
