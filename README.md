# ReplayTest
Distributed replay of transactions. Distributed to run entire history in a short period of time.

## Description
Spins up many hosts that work together to process the entire history of EOS. Each instance is designated to test a unique range of blocks. At the end of the range the integrity hash is checked against a previous run to ensure validity of the replay.

See [High Level Design](docs/high-level-design.md). The service has two components an orchestrator node, and many replay nodes. The replay nodes connect to the orchestrator via HTTP to fetch job configuration and update status.

For a description of the HTTP calls supported by the orchestrator see [HTTP Service Calls](docs/http-service-calls.md)

## Orchestrator Setup
First you need to setup an orchestrator, then you need to setup your relay nodes. Best way to do this is through the AWS portal. *Not sure of the roles and permissions you need to start these services. Need to fill in that information* If you would like to configure your own launch template see [AWS Host Setup](docs/AWS-Host-Setup.md)

To setup your orchestrator node. Go to EC2 Instances
![EC2Instance](docs/images/CDEC2Instance.png)

Select launch instance from template
![LaunchTemplace](docs/images/CDLaunchTemplate.png)

Select `LowEndOrchestrator` and use the default template.
![OrchTemplaceSelect](docs/images/CDOrchTemplateSelect.png)

## Updating Orchestrator Job Configuration
By default the setup will spin up a webservice with [test data](meta-data/test-simple-jobs.json). To change the job configuration you need to create your own JSON configuration, and restart the service to use the new JSON.
- Create your own JSON following the example formate from `test-simple-jobs.json`
- Upload the file to the orchestrator node
- Log into the orchestrator node as `ubuntu` user
- Kill the existing service named `python3 ... webservice.py`
- Restart with your configuration `python3 $HOME/replay-test/orchestration-service/web_service.py --config my-config.json --host 0.0.0.0 &`

## Replay Setup
You can spin up as many replay nodes as you need. Each replay node is designed to use one replay slice configuration as provided in the JSON configuration file. If you have 100 replay slices configured you can utilize up to 100 replay hosts.

To setup your orchestrator node. Go to EC2 Instances
![CDEC2Instance](docs/images/CDEC2Instance.png)

Select launch instance from template
![LaunchTemplace](docs/images/CDLaunchTemplate.png)

Select `ChickenReplayHost` and use the default template.
![ReplayTemplaceSelect](docs/images/CDReplayTemplateSelect.png)

Once your replay host is setup you need to ssh into the host and start the job.
- Grab the private IP of the orchestrator node
- SSH in as user `enf-replay`
- Run `$HOME/replay-test/replay-client/start-nodeos-run-replay X.X.X.X`
   - replacing the argument with the orchestrator node private IP
   - optionally provide a second argument for the orchestrator webservice port

**Alternative**: you can start a replay node on the command line from the orchestrator node. See [an example](scripts/run-replay-instance.sh).

## Web Dashboard
You can see the status of jobs, configuration, and summary of replay status by using the webservice on the orchestrator node. Navigate to `http://orchestor.example.com:4000/`.

Many HTTP calls support HTML, JSON, and Text responses. Look at [HTTP Service Calls](docs/http-service-calls.md) for other URL options and Accept encoding options.

## Termination of Replay Nodes
Replay nodes are not automatically terminated. To save on hosting costs, it is advisable to terminate the nodes after the replay tests are completed.

## Testing
For testing options see [Running Tests](docs/running-tests.md)

## Generating Manifests
The python script `replay-test/scripts/generate_manifest_from_eosnation.py` will build a manifest off the list of eos nation snapshots.

`python3 generate_manifest_from_eosnation.py --source-net mainnet > full-mainnet-run.json`

### Options
- `--source-net` Defaults to `mainnet`. Which chain to target. Options include mainnet, kylin, and jungle
- `--leap-version` Defaults to `5.0.0`. Specify the version of leap to use from the builds
- `--snapshot-version` Defaults to v6.
- `--upload-snapshots` Flag takes no values, and defaults to false. This uploads snapshots to AWS S3. Must have `aws cli` and permission to upload.
