#!/usr/bin/env bash

# setup aws cli
sudo apt update
apt install unzip
sudo apt install unzip
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" && unzip awscliv2.zip
sudo ./aws/install

BRANCH="ehp/gh-3-aws-setup"

# get the scripts
if [ -n "$BRANCH" ]; then
  git clone -b "$BRANCH" https://github.com/eosnetworkfoundation/replay-test
else
  git clone https://github.com/eosnetworkfoundation/replay-test
fi
