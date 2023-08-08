#!/usr/bin/env bash

TUID=$(id -ur)
USER="enf-replay"
PUBLIC_KEY="${1}"

# must be root to run
if [ "$TUID" -ne 0 ]; then
  echo "Must run as root"
  exit
fi

# does the user already exist
if getent passwd "${USER}" > /dev/null 2>&1; then
    echo "yes the user exists"
    exit 0
else
    echo "Creating user ${USER}"
fi


KEY_SIZE=$(echo "${PUBLIC_KEY}" | cut -d' ' -f2 | wc -c)
if [ "$KEY_SIZE" -lt 33 ]; then
    echo "Invalid public key"
    exit 1
fi

# gecos non-interactive
sudo adduser "${USER}" --disabled-password --gecos ""
sudo -i -u "${USER}" mkdir .ssh && chmod 700 .ssh \
  && touch .ssh/authorized_keys \
  && chmod 600 .ssh/authorized_keys \
  && echo "$PUBLIC_KEY" >> .ssh/authorized_keys
