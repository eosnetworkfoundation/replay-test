#!/usr/bin/env bash

# either "started" or "stopped"
TYPE=${1:-started}
NODEOS_DIR=${2:-/data/nodeos}

grep "chain database ${TYPE} with hash" "${NODEOS_DIR}"/log/nodeos.log | cut -d: -f5 | tr -d '[:space:]'
