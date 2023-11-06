#!/usr/bin/env bash

USER="enf-replay"

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

# remove data
rm -rf /data/nodeos

# remove package
rm /home/${USER:?}/*.deb

# clean out directory
rm -rf /home/"${USER:?}"/*
rm -rf /home/"${USER:?}"/.*
