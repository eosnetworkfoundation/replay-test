#!/usr/bin/env bash

# install python lib
pip install tomli

# install nodeos
replay-client/install-nodeos.sh 5.0.0-rc3

# create directories
replay-client/create-nodeos-dir-struct.sh ./config/

# setup path
PATH=home/enf-replay/nodeos/usr/bin/:${PATH}
export PATH

# grab down some snapshots
SNAP="snapshot-2018-12-05-16-eos-v6-0030527359.bin.zst"
START_NUM=$(echo $SNAP | cut -d'-' -f8 | cut -d'.' -f1)
let END_NUM=START_NUM+1000
aws s3 cp s3://chicken-dance/mainnet/snapshots/${SNAP} /data/nodeos/snapshot
zstd -d /data/nodeos/snapshot/*.zst

# copy in first blocks log
replay-client/manage_blocks_log.sh /data/nodeos "restore" $START_NUM "some-end-num" "s3://chicken-dance/mainnet/snapshots/${SNAP}"

# start with a snapshot
nodeos --snapshot /data/nodeos/snapshot/${SNAP} \
  --data-dir "${NODEOS_DIR}"/data/ \
  --config "${CONFIG_DIR}"/sync-config.ini \
  --terminate-at-block ${END_NUM}

# ok now we are ready to run
