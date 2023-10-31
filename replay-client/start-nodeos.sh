#!/usr/bin/env bash

SNAPSHOT_TYPE="${1}"
SNAPSHOT_LOCATION="${2}"
END_BLOCK="${3}"

USER=enf-replay
if [ $SNAPSHOT_TYPE = "s3" ]; then
  aws s3 cp "${SNAPSHOT_LOCATION}" /tmp/snapshot.dat
else
  echo "unknown snapshot type ${SNAPSHOT_TYPE}"
  exit 127
fi

nodeos \
   --config-dir /home/"${USER}"/config/ \
   --data-dir /home/"$USER"/data/ \
   --snapshot /tmp/snapshot.dat \
   --truncate-at-block ${END_BLOCK} &> /home/"${USER}"/log/nodeos.log &
