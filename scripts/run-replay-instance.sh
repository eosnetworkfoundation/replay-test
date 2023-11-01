#!/usr/bin/env bash

aws ec2 run-instances --image-id ami-053b0d53c279acc90 \
--instance-type t2.micro \
--security-group-ids sg-04f895bd6442b69b5 \
--key-name aws-chicken-start \
--subnet-id subnet-0b9517f11e9684b3b \
--iam-instance-profile Arn=arn:aws:iam::087045697350:instance-profile/ReplayOrchestration \
--user-data file:///home/ubuntu/replay-test/scripts/replay-node-bootstrap.sh \
--dry-run

aws ec2 run-instances --image-id ami-053b0d53c279acc90 \
--instance-type t2.micro \
--security-group-ids sg-04f895bd6442b69b5 \
--key-name aws-chicken-start \
--iam-instance-profile Name=ReplayOrchestration \
--subnet-id subnet-0b9517f11e9684b3b \
--user-data file:///home/ubuntu/replay-test/scripts/replay-node-bootstrap.sh \
--count 1 \
--dry-run
