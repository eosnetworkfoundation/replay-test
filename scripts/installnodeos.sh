#!/usr/bin/env bash

TUID=$(id -ur)

# must not be root to run
if [ "$TUID" -eq 0 ]; then
  echo "Trying to run as root user exiting"
  exit
fi


mkdir ~/config
mkdir ~/data
mkdir ~/log
