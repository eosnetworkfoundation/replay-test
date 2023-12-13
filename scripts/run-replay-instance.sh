#!/usr/bin/env bash

# launch replay nodes from command line

HOME="/home/ubuntu"
INSTANCE_FILE="${HOME}/aws-replay-instances.txt"
SCRIPTS_DIR="${HOME}/replay-test/scripts"
AWS_REPLAY_TEMPLATE="ChickenReplayHost"
AWS_REPLAY_TEMPLATE_VERSION="13"

NUM_INSTANCES=${1:-1}
DRY_RUN=${2}

if [ -n "$DRY_RUN" ]; then
  DRY_RUN="--dry-run"
else
  DRY_RUN=""
fi

# modify user data script to stuff in private ip of orchestration server
ORCH_IP=$(sh /home/ubuntu/replay-test/scripts/get_private_ip.sh)
sed "s^# MACRO_P echo \$ORCH_IP^echo $ORCH_IP^" "${SCRIPTS_DIR}/replay-node-bootstrap.sh" > /tmp/replay-node-bootstrap.sh
mv /tmp/replay-node-bootstrap.sh "${SCRIPTS_DIR}/replay-node-bootstrap.sh"

aws ec2 run-instances --launch-template LaunchTemplateName=${AWS_REPLAY_TEMPLATE},Version=${AWS_REPLAY_TEMPLATE_VERSION} \
--user-data file://"${SCRIPTS_DIR}"/replay-node-bootstrap.sh \
--count $NUM_INSTANCES $DRY_RUN > /tmp/aws-run-instance-out.json
