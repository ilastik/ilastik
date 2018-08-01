#!/bin/bash
# Script for automatic creation of an ilastik-devenv.
# mainly following the guide on https://github.com/ilastik/ilastik-build-conda
# for this script to work, conda has to be in your path
# tested with conda v4.5.4

usage ()
{
  echo "Usage : $0 [options] <ENVIRONMENT_NAME> [<ILASTIK-META_LOCAL_SOURCE_PATH>]"
  echo
  echo "valid options (each can be invoked multiple times:"
  echo "  -a <additional_package>"
  echo "  -c <additional_channel>  # additional channels have higher priority"
  echo
  echo "If ILASTIK-META_LOCAL_SOURCE_PATH is not given, package"
  echo "    ilastik-meta"
  echo "will not be removed"
  echo
  exit
}

NEW_CHANNELS=()
ADDITIONAL_PACKAGES=()

CHANNELS=""
PACKAGES="ilastik-dependencies-no-solvers"

while getopts ":c:a:h" flag; do
  case "$flag" in
    c) NEW_CHANNELS+=("$OPTARG");;
    a) ADDITIONAL_PACKAGES+=("$OPTARG");;
    h) usage; exit 0;;
    \?) echo "unknown option"; usage; exit 1;;
  esac
done

if [ ${#NEW_CHANNELS[@]} -gt 0 ]
then
  for ch in "${NEW_CHANNELS[@]}"; do
    CHANNELS+="-c ${ch} "
  done
else
  CHANNELS+="-c ilastik-forge "
fi
CHANNELS+="-c conda-forge"

if [ ${#ADDITIONAL_PACKAGES[@]} -gt 0 ]
then
  for package in "${ADDITIONAL_PACKAGES[@]}"; do
    PACKAGES+=" ${package} "
  done
fi

ENV_NAME=${@:$OPTIND:1}

if [ -z "${ENV_NAME}" ]
then
    echo "No environment name specified!"
    usage
    exit 1
fi

ILASTIK_META_SOURCE=${@:$OPTIND+1:1}

# assuming that miniconda is already installed:
CONDA_ROOT=$(conda info --root)
source "${CONDA_ROOT}"/bin/activate root
echo "creating environment ${ENV_NAME}"
echo "Using the following channels: ${CHANNELS}"
echo "installing the following packages ${PACKAGES}"

conda create -y -n "${ENV_NAME}" "${CHANNELS}" "${PACKAGES}"


if [ "${ILASTIK_META_SOURCE}" != "" ]
then
    echo "linking to existing sources in ${ILASTIK_META_SOURCE}"
    DEV_PREFIX=${CONDA_ROOT}/envs/${ENV_NAME}
    conda remove -y -n "${ENV_NAME}" ilastik-meta
    # Re-install ilastik-meta.pth
    cat > "${DEV_PREFIX}"/lib/python3.6/site-packages/ilastik-meta.pth << EOF
../../../ilastik-meta/lazyflow
../../../ilastik-meta/volumina
../../../ilastik-meta/ilastik
EOF
    cd "${DEV_PREFIX}" && ln -s "${ILASTIK_META_SOURCE}"
fi
