#!/usr/bin/env bash

USER=enf-replay
nodeos --config-dir /home/"${USER}"/config/ --data-dir /home/"$USER"/data/ &> /home/"${USER}"/log/nodeos.log &
