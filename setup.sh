#!/bin/bash
# setup python so that it works properly

# get the absolute directory of this script
ABS_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"

# append fitConfig dir to python path
PYTHONPATH=${PYTHONPATH}:${ABS_SCRIPT_DIR}/fitConfig
