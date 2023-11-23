#!/usr/bin/env bash

# simple wrapper script used by cronjob to run replay
USER="enf-replay"

ORCH_IP=172.31.79.129
/home/${USER}/replay-test/replay-client/start-nodeos-run-replay.sh ${ORCH_IP} > /home/${USER}/last-replay.log 2>&1
