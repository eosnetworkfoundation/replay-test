#!/usr/bin/env bash

CONFIG="${1}"

TUID=$(id -ur)

# must not be root to run
if [ "$TUID" -eq 0 ]; then
  echo "Trying to run as root user exiting"
  exit
fi

mkdir ~/config
mkdir ~/data
mkdir ~/snapshot
mkdir ~/log

cp $CONFIG ~/config
