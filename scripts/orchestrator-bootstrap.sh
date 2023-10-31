#!/usr/bin/env bash

# setup aws cli
sudo apt update
sudo apt install -y unzip python3 python3-pip
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" && unzip awscliv2.zip
sudo ./aws/install

# get the scripts
git clone https://github.com/eosnetworkfoundation/replay-test
pip install datetime enum argparse werkzeug

cd replay-test/orchestration-service || exit
python3 ./web_service.py --config "../meta-data/test-simple-jobs.json" --host 0.0.0.0 &
