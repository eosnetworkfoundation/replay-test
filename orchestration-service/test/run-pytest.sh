#!/usr/bin/env bash

export PYTHONPATH=..:meta-data:orchestration-service:orchestration-service/test:$PYTHONPATH
# setup test file for persistance testing
cp ../../meta-data/test-simple-jobs.json ../../meta-data/test-modify-jobs.json
pytest test_*.py
# dump and remove file used for persistance testing
cat ../../meta-data/test-modify-jobs.json
rm ../../meta-data/test-modify-jobs.json
