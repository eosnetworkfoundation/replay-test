#!/usr/bin/env bash

export PYTHONPATH=..:meta-data:orchestration-service:orchestration-service/test:$PYTHONPATH
# setup test file for persistance testing
cp ../../meta-data/test-simple-jobs.json ../../meta-data/test-modify-jobs.json
pytest test_replay_configuration.py
pytest test_jobs_class.py
# dump and remove file used for persistance testing
DIFF_CNT=$(diff ../../meta-data/test-simple-jobs.json ../../meta-data/test-modify-jobs.json | grep "^>" | wc -l)
if [ "$DIFF_CNT" -lt 1 ]; then
  echo "ERROR meta-data File was not modified"
  cat ../../meta-data/test-modify-jobs.json
  exit 1
fi
if [ "$DIFF_CNT" -gt 15 ]; then
  echo "Meta-data file was not updated correctly"
  cat ../../meta-data/text-modify-jobs.json
  exit 1
fi
rm ../../meta-data/test-modify-jobs.json

# integration tests start up service
{ python3 ../web_service.py --config "../../meta-data/test-simple-jobs.json" --host 127.0.0.1 > /dev/null 2>&1 & }
WEB_SERVICE_PID=$!

# prevent tests running before service is up
sleep 3

# now test web service
pytest test_web_service.py

# shutdown service
kill "$WEB_SERVICE_PID"
