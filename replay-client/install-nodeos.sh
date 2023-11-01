#!/usr/bin/env bash

LEAP_VERSION="${1}"
OS="ubuntu22.04"
v4_DEB_FILE="leap_""${LEAP_VERSION}"-"${OS}""_amd64.deb"
v5_DEB_FILE="leap_""${LEAP_VERSION}""_amd64.deb"
if [ ${LEAP_VERSION:0:1} == "4" ]; then
  DEB_URL="https://github.com/AntelopeIO/leap/releases/download/v""${LEAP_VERSION}"/"${v4_DEB_FILE}"
  DEB_FILE=${v4_DEB_FILE}
else
  DEB_URL="https://github.com/AntelopeIO/leap/releases/download/v""${LEAP_VERSION}"/"${v5_DEB_FILE}"
  DEB_FILE=${v5_DEB_FILE}
fi

TUID=$(id -ur)
# must be root to run
if [ "$TUID" -ne 0 ]; then
  echo "Must run as root"
  exit
fi

## root setup ##
# clean out un-needed files
for not_needed_deb_file in /tmp/leap_[0-9]*.deb
do
  if [ "${not_needed_deb_file}" != /tmp/"${DEB_FILE}" ]; then
    echo "removing ${not_needed_deb_file}"
    rm -rf ${not_needed_deb_file}
  fi
done

# download file if needed
if [ ! -f /tmp/"${DEB_FILE}" ]; then
  wget --directory-prefix=/tmp "${DEB_URL}"
fi
# install nodeos
dpkg -i /tmp/"${DEB_FILE}"
