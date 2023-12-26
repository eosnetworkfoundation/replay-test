#!/usr/bin/env bash

for i in /data/nodeos/data/snapshots/snapshot-*.bin.zst
do
   echo $i
   aws s3 cp $i s3://chicken-dance/mainnet/hand-built-snapshots/
   if [ $? -eq 0 ]; then
      mv $i /data/nodeos/data/snapshots/archive
   fi
done
