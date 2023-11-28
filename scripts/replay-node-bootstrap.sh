#!/usr/bin/env bash

# User-Data Script
# Run as root off launch template

## packages ##
apt-get update >> /dev/null
apt-get install -y git unzip jq curl python3 python3-pip

## aws cli ##
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "/tmp/awscliv2.zip"
unzip /tmp/awscliv2.zip -d /tmp/ >> /dev/null
/tmp/aws/install
rm -rf /tmp/aws /tmp/awscliv2.zip

## new user ##
USER="enf-replay"
PUBLIC_KEY="ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIPbQbXU9uyqGwpeZxjeGR3Yqw8ku5iBxaKqzZgqHhphS support@eosnetwork.com - ANY"

## does the user already exist ##
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

## gecos non-interactive ##
adduser "${USER}" --disabled-password --gecos ""
sudo -u "${USER}" -- sh -c "mkdir /home/enf-replay/.ssh && chmod 700 /home/enf-replay/.ssh && touch /home/enf-replay/.ssh/authorized_keys && chmod 600 /home/enf-replay/.ssh/authorized_keys"
echo "$PUBLIC_KEY" | sudo -u "${USER}" tee -a /home/enf-replay/.ssh/authorized_keys

## setup data device ##
echo "setting up ext4 /dev/xvdb volume"
mkdir /data
mkfs.ext4 /dev/nvme1n1
mount -o rw,acl,user_xattr /dev/nvme1n1 /data
chmod 777 /data

## git scripts for enf-user ##
sudo -i -u "${USER}" git clone https://github.com/eosnetworkfoundation/replay-test

## python packages ##
sudo -i -u "${USER}" pip install bs4

## create cron tab ##
# random number of mins to space out startups across many replay nodes
random_num=$(( RANDOM % 10 ))
mins=""
for m in 0 1 2 3 4 5; do
  mins="$mins""$m$random_num"
  if [ $m -lt 5 ]; then
    mins="$mins"","
  fi
done
# mins is something like 04,14,24,34,44,54
# run 6 times every hour
# cron job manages lock file will exit if existing process is running
echo "${mins} * * * * /home/${USER}/replay-test/replay-client/replay_wrapper_script.sh" | crontab -u ${USER} - && echo "Cron job added successfully"
