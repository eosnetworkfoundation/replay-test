#!/usr/bin/env bash

# launch replay nodes from command line
# currently restricted by IAM permissions and NOT usable

NUM_INSTANCES=${1:-1}
DRY_RUN=${2}

if [ -n "$DRY_RUN" ]; then
  DRY_RUN="--dry-run"
else
  DRY_RUN=""
fi

#aws ec2 run-instances --launch-template LaunchTemplateName=ChickenReplayHost,Version=9 \
#--user-data file:///home/ubuntu/replay-test/scripts/replay-node-bootstrap.sh \
#--count $NUM_INSTANCES $DRY_RUN
