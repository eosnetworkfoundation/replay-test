# High Level Design Document

This service is designed to run multiple hosts to download, install, run nodeos. Following that the host will load a snapshot and start syncing blocks to a specific block number. Once that process is finished the host will report back the integrity hash representing nodeos' final state.

## Overview
Once replay hosts are spun up they contact the orchestration service to get the information needed to run their jobs. The replay hosts update the orchestration service with their progress and current status. The orchestration service is single threaded, and has checks to ensure there are not overwrites or race conditions. The replay nodes use increasing backoffs to avoid sending too many simultaneous requests.

```mermaid
C4Context
title Overview of Replay Testing System

Person(enfEmployee, "Authorized ENF Person")
SystemQueue(orchestrator, "Orchestrator", "Web Service that holds the state of jobs")

System_Boundary(nodes, "Replay Nodes") {
  System(replayA,"Replay Host A", "Host that start nodeos and run transactions")
  System(replayB,"Replay Host B", "Host that start nodeos and run transactions")
  System(replayC,"Replay Host C", "Host that start nodeos and run transactions")
  System(replayD,"Replay Host D", "Host that start nodeos and run transactions")
}

Rel(enfEmployee, orchestrator, "gets job status", "HTTP")
UpdateRelStyle(enfEmployee, orchestrator, $offsetY="-35", $offsetX="-40")
Rel(replayA, orchestrator, "gets jobs/sets status", "HTTP")
UpdateRelStyle(replayA, orchestrator, $offsetY="-35", $offsetX="+10")
Rel(replayB, orchestrator, "gets jobs/sets status", "HTTP")
UpdateRelStyle(replayB, orchestrator, $offsetY="-35")
Rel(replayC, orchestrator, "gets jobs/sets status", "HTTP")
UpdateRelStyle(replayC, orchestrator, $offsetY="-35")
Rel(replayD, orchestrator, "gets jobs/sets status", "HTTP")
UpdateRelStyle(replayD, orchestrator, $offsetY="-35", $offsetX="+30")
Rel(replayD, orchestrator, "gets jobs/sets status", "HTTP")
```


## Sequence
Fairly straight forward, the relay host picks up a job, and updates the jobs status while it works through the lifecycle. The relay host will update the progress by updating the last block processed. Full list of status is found here. https://github.com/eosnetworkfoundation/replay-test/blob/311f13439542542c0b24e313a26a012eb59a8a6c/orchestration-service/job_status.py#L9-L15

```mermaid

sequenceDiagram
    participant Relay as Replay Host
    participant Orch as Orchestrator
    Relay->>Orch: GET /job?nextjob
    Orch->>Relay: json_job
    Relay->>Orch: POST /job status=STARTED
    Orch->>Relay: 200 SUCCESS
    Relay->>Orch: POST /job status=WORKING
    Orch->>Relay: 200 SUCCESS
    Relay->>Orch: POST /job last_block_processed=XXXX
    Orch->>Relay: 200 SUCCESS
    Relay->>Orch: POST /job status=COMPLETE, actual_integrity_hash=SHA_256, end_time=, last_block_processed=XXXX
    Orch->>Relay: 200 SUCCESS
```