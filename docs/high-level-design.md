# High Level Design Document

This service is designed to run multiple hosts to download, install, run nodeos. Following that the host will load a snapshot and start syncing blocks to a specific block number. Once that process is finished the host will report back the integrity hash representing nodeos' final state.

## Overview 
Once replay hosts are spun up they contact the orchestration service to get the information needed to run their jobs. The replay hosts update the orchestration service with their progress and current status. The orchestration service is single threaded, and has checks to ensure there are not overwrites or race conditions. The replay nodes use increasing backoffs to avoid sending too many simultaneous requests. 

```mermaid
C4Context
title Overview of Replay Testing System

Person(enfEmployee, "Authorized ENF Employee/Contractor")
SystemQueue(orchestration, "Web Service that holds the state of jobs")

System_Boundary(nodes, "Replay Nodes") {
  System(replayA,"Replay Host A", "Host that start nodeos and run transactions")
  System(replayB,"Replay Host B", "Host that start nodeos and run transactions")
  System(replayC,"Replay Host C", "Host that start nodeos and run transactions")
  System(replayD,"Replay Host D", "Host that start nodeos and run transactions")
}

Rel(enfEmployee, orchestration, "gets job status", "HTTP")
UpdateRelStyle(enfEmployee, orchestration, $offsetX="-50", $offsetY="+10")
Rel(replayA, orchestration, "gets jobs/sets status", "HTTP")
UpdateRelStyle(replayA, orchestration, $offsetY="-45")
Rel(replayB, orchestration, "gets jobs/sets status", "HTTP")
UpdateRelStyle(replayB, orchestration, $offsetY="-45")
Rel(replayC, orchestration, "gets jobs/sets status", "HTTP")
UpdateRelStyle(replayC, orchestration, $offsetY="-45")
Rel(replayD, orchestration, "gets jobs/sets status", "HTTP")
UpdateRelStyle(replayD, orchestration, $offsetY="-45")
Rel(replayD, orchestration, "gets jobs/sets status", "HTTP")
UpdateRelStyle(replayD, orchestration, $offsetY="-45")
```
