#!/usr/bin/env bash

# integration tests start up service
{ python3 ../../orchestration-service/web_service.py --config "../../meta-data/test-simple-jobs.json" --host 127.0.0.1 > /dev/null 2>&1 & }
WEB_SERVICE_PID=$!

# prevent tests from running before web service is up
sleep 3

# now test web service
# pop job make sure id comes back
JOBID=$(python3 ../../replay-client/job_operations.py --operation pop | python3 ../../replay-client/parse_json.py job_id )
if [ -z $JOBID ]; then
  echo "Error POP Job Failed"
  # shutdown service
  kill "$WEB_SERVICE_PID"
  exit 1
fi
# check status
COUNT=$(curl -s http://127.0.0.1:4000/job\?jobid\=${JOBID} | grep STARTED | wc -l)
if [ $COUNT -ne 1 ]; then
  echo "ERROR Job did not have STARTED status"
  # shutdown service
  kill "$WEB_SERVICE_PID"
  exit 1
fi
# check status changed
python3 ../../replay-client/job_operations.py --operation update-status --status WORKING --job-id $JOBID
COUNT=$(curl -s http://127.0.0.1:4000/job\?jobid\=${JOBID} | grep WORKING | wc -l)
if [ $COUNT -ne 1 ]; then
  echo "ERROR Job did not have WORKING status"
  # shutdown service
  kill "$WEB_SERVICE_PID"
  exit 1
fi
python3 ../../replay-client/job_operations.py --operation update-progress --block-processed 20 --job-id $JOBID
if [ $? -eq 0 ]; then
   echo "SUCCESS"
fi

# shutdown service
kill "$WEB_SERVICE_PID"
