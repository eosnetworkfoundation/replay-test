# Running Tests

## Overview
There are two sets of tests.
- Orchestration Service Tests
- Replay Script Tests

Manually running tests with the web service are covered at the end of this document.

## Orchestration Service Tests

Runs unit tests for the python classes, and runs an integration test for the web service.

### How to Run

The last test `test_web_service.py` can be flaky, and if you see *connection refused* errors try re-running the test.
The web service test will start up a web service on loopback, 127.0.0.1 port 4000.

```
sudo apt install -y unzip python3 python3-pip
pip install datetime argparse werkzeug
cd orchestration-service/test
./run-pytest.sh
```

### Details
This runs the following test files.
- `test_replay_configuration.py` - tests the replay config class
- `test_jobs_class.py` - tests the jobs class
- `test_web_service` - starts the web service and runs integration test
- `test_summary_report` - unit tests to make sure the summary report can be generated

## Replay Tests
Runs additional integration tests, testing the client side code. The replay service is mostly shell scripts. `job_operations.py` was created to perform more sophisticated job related HTTP operations. `config_operations.py` is very similar, its sole purpose it to take the integrity hash, from a snapshot, and update the configuration on the orchestration service. See [config POST](https://github.com/eosnetworkfoundation/replay-test/blob/main/docs/http-service-calls.md#post-1) for details on the configuration operations.

### How to Run
The web service test will start up a web service on loopback, 127.0.0.1 port 4000.
Look for `SUCCESS` as the very last output from the script.

```
sudo apt install -y unzip python3 python3-pip
pip install datetime argparse werkzeug
cd replay-client/tests
./run.sh
```

### Details
`run.sh` shows an example of using `job_operations.py` from a shell script.

## Manually Run
You can manually run the web service, and perform operations while watching an HTML status page.

### Start the Service
`python3 ./orchestration-service/web_service.py --config "./meta-data/test-simple-jobs.json" --host 127.0.0.1`

### View status
Point your browser to `http://127.0.0.1:4000/status`

### Run Operations
This will pop a job off the stack, and change the status to `STARTED`
`python3 scripts/job_operations.py --operation pop`
Look for the `jobid` in the JSON returned. You will need this for future operations.
Next refresh the [status page](http://127.0.0.1:4000/status) and look for a job with status `STARTED`.

Another operation you can run is
`python3 scripts/job_operations.py --operation update-progress --block-processed 20 --job-id $JOBID`

### Curl Command Line
You can perform operations on the command line. Here is an example to get a job
`curl -s http://127.0.0.1:4000/job\?jobid\=${JOBID}`
