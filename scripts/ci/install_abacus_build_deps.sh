#!/usr/bin/env bash
set -euo pipefail

# This is the ordinary hosted CPU/LCAO toolchain, not a workstation toolchain.
# Keep this list in sync with the dependency inventory in build-provenance.json.
if [[ $# -ne 0 ]]; then
  echo 'usage: install_abacus_build_deps.sh' >&2
  exit 2
fi

# shellcheck source=/dev/null
source /etc/os-release
if [[ "${ID:-}" != ubuntu || "${VERSION_ID:-}" != 24.04 ]]; then
  echo 'ABACUS CI dependency recipe requires Ubuntu 24.04' >&2
  exit 2
fi

packages=(
  build-essential
  cmake
  git
  libopenmpi-dev
  openmpi-bin
  libfftw3-dev
  libopenblas-dev
  libscalapack-openmpi-dev
  libcereal-dev
  pkg-config
  python3
)

if [[ ${EUID} -eq 0 ]]; then
  apt=(env DEBIAN_FRONTEND=noninteractive apt-get)
else
  command -v sudo >/dev/null || {
    echo 'sudo is required to install ABACUS CI dependencies' >&2
    exit 2
  }
  apt=(sudo env DEBIAN_FRONTEND=noninteractive apt-get)
fi

"${apt[@]}" update
"${apt[@]}" install -y --no-install-recommends "${packages[@]}"
dpkg-query -W -f='${binary:Package}=${Version}\n' "${packages[@]}"
