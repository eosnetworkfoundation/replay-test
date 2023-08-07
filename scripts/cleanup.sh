#!/usr/bin/env bash

TUID=$(id -ur)
USER="enf-replay"

# must be root to run
if [ "$TUID" -ne 0 ]; then
  echo "Must run as root"
  exit
fi

# aggressivley terminate nodeos
# start nicely then get mean
for signal in 15 9
do
  PID=$(ps -u "${USER:?}" | grep nodeos | sed -e 's/^[[:space:]]*//' | cut -d" " -f1)
  if [ -n "$PID" ]; then
    kill -"${signal}" $PID
    sleep 5
  fi
done

# remove package
dpkg -r leap

# clean out directory
rm -rf /home/"${USER:?}"/*

# remove user
sudo deluser "${USER:?}"
