#!/usr/bin/env bash

# launch replay nodes

NUM_INSTANCES=${1:-1}
DRY_RUN=${2}

if [ -n "$DRY_RUN" ]; then
  DRY_RUN="--dry-run"
else
  DRY_RUN=""
fi

# modify user data script to stuff in private ip of orchestration server
ORCH_IP=$(sh /home/ubuntu/replay-test/scripts/get_private_ip.sh)
sed "s^# MACRO_P echo \$ORCH_IP^echo $ORCH_IP^" /home/ubuntu/replay-test/scripts/replay-node-bootstrap.sh > /tmp/replay-node-bootstrap.sh
mv /tmp/replay-node-bootstrap.sh /home/ubuntu/replay-test/scripts/replay-node-bootstrap.sh

aws ec2 run-instances --launch-template LaunchTemplateName=ChickenReplayHost,Version=9 \
--user-data file:///home/ubuntu/replay-test/scripts/replay-node-bootstrap.sh \
--count $NUM_INSTANCES $DRY_RUN
