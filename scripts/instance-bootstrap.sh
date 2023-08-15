#!/usr/bin/env bash

BRANCH="ehp/gh-3-aws-setup"

# update
apt update
# get the scripts
if [ -n "$BRANCH" ]; then
  git clone -b ehp/gh-3-aws-setup https://github.com/eosnetworkfoundation/replay-test
else
  git clone https://github.com/eosnetworkfoundation/replay-test
fi

# setup
sudo ./replay-test/scripts/nodeos-setup.sh "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIPbQbXU9uyqGwpeZxjeGR3Yqw8ku5iBxaKqzZgqHhphS support@eosnetwork.com - ANY"
