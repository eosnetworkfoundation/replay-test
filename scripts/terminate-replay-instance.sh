#!/usr/bin/env bash

# kill off instances by ID.
# When ALL provided terminates all instances in the file ~/aws-replay-instances.txt

INSTANCE_FILE="/home/ubuntu/aws-replay-instances.txt"
TERMINATE_CMD="aws ec2 terminate-instances --instance-ids"

INSTANCE_ID=${1:ALL}
DRY_RUN=${2}

if [ -n "$DRY_RUN" ]; then
  DRY_RUN="--dry-run"
else
  DRY_RUN=""
fi

# All instances 
if [ "$INSTANCE_ID" == "ALL" ]; then
  if [ -f "$INSTANCE_FILE" ]; then
    ALL_INSTANCES=$(paste -s -d ' ' "$INSTANCE_FILE")
    "$TERMINATE_CMD" "$ALL_INSTANCES"
  fi
# Single instance
else
  if [ -n "$INSTANCE_ID" ]; then
     "$TERMINATE_CMD" "$INSTANCE_ID"
  else
    echo "Must provide AWS instance ID or ALL as first arg"
    exit 1
  fi
fi
