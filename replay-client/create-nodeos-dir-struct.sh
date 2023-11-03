#!/usr/bin/env bash

CONFIG="${1}"
TUID=$(id -ur)

# must not be root to run
if [ "$TUID" -eq 0 ]; then
  echo "Trying to run as root user exiting"
  exit
fi

[ ! -d /data/nodeos ] && mkdir /data/nodeos
[ ! -d /data/nodeos/config ] && mkdir /data/nodeos/config
[ ! -d /data/nodeos/data ] && mkdir /data/nodeos/data
[ ! -d /data/nodeos/snapshot ] && mkdir /data/nodeos/snapshot
[ ! -d /data/nodeos/log ] && mkdir /data/nodeos/log

FILENAME=$(basename "${CONFIG}")
[ ! -f /data/nodeos/config/"${FILENAME}" ] && cp $CONFIG /data/nodeos/config
