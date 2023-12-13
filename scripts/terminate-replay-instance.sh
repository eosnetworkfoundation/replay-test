#!/usr/bin/env bash

# kill off instances by ID.
# When ALL provided terminates all instances in the file ~/aws-replay-instances.txt

INSTANCE_FILE="/home/ubuntu/aws-replay-instances.txt"

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
    aws ec2 terminate-instances --instance-ids "$ALL_INSTANCES" "$DRY_RUN"
    # not dry-run remove file
    if [ -z "$DRY_RUN" ]; then
      rm "$INSTANCE_FILE"
    fi
  fi
# Single instance
else
  if [ -n "$INSTANCE_ID" ]; then
     aws ec2 terminate-instances --instance-ids "$INSTANCE_ID" "$DRY_RUN"
  else
    echo "Must provide AWS instance ID or ALL as first arg"
    exit 1
  fi
fi
