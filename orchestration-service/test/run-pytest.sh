#!/usr/bin/env bash

export PYTHONPATH=..:meta-data:orchestration-service:orchestration-service/test:$PYTHONPATH
pytest test_*.py
