#!/usr/bin/env bash

export PYTHONPATH=..:meta-data:orchestration-service:orchestration-service/test:$PYTHONPATH
# setup test file for persistance testing
#cp ../../meta-data/test-simple-jobs.json ../../meta-data/test-modify-jobs.json
#pytest test_replay_configuration.py
#pytest test_jobs_class.py
# dump and remove file used for persistance testing
#cat ../../meta-data/test-modify-jobs.json
#rm ../../meta-data/test-modify-jobs.json



# integration tests start up service
python3 ../web_service.py --config "../../meta-data/test-simple-jobs.json" --host 127.0.0.1 &
WEB_SERVICE_PID=$!

# now test web service
pytest test_web_service.py

# shutdown service
kill "$WEB_SERVICE_PID"
