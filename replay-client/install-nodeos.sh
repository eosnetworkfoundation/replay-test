#!/usr/bin/env bash

# install nodeos locally 

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

## root setup ##
# clean out un-needed files
for not_needed_deb_file in "${HOME:?}"/leap_*.deb
do
  if [ "${not_needed_deb_file}" != "${HOME:?}"/"${DEB_FILE}" ]; then
    echo "Removing not needed deb ${not_needed_deb_file}"
    rm -rf ${not_needed_deb_file}
  fi
done

# download file if needed
if [ ! -f "${HOME:?}"/"${DEB_FILE}" ]; then
  wget --directory-prefix=${HOME} "${DEB_URL}" 2> /dev/null
fi

# install nodeos locally
echo "Installing nodeos ${LEAP_VERSION} locally"
[ -d "${HOME:?}"/nodeos ] && rm -rf "${HOME:?}"/nodeos
mkdir "${HOME:?}"/nodeos
dpkg -x "${HOME:?}"/"${DEB_FILE}" "${HOME:?}"/nodeos
