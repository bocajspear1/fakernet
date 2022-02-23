#!/bin/bash

COLOR_RED="\e[1;31m"
COLOR_BLUE="\e[1;34m"
COLOR_GREEN="\e[1;32m"
COLOR_ORANGE="\e[1;33m"
COLOR_RESET="\e[0m"

echo -e "${COLOR_GREEN}Starting Tests!${COLOR_RESET}"
cd /opt/fakernet 
source ./venv/bin/activate 


export FAKERNET_DEBUG=1

echo -e "${COLOR_BLUE}Cleaning...${COLOR_RESET}"
python3 tools/full-clean.py -f
python3 tools/clean-images.py -f
echo -e "${COLOR_BLUE}Building...${COLOR_RESET}"
python3 -u build.py
echo -e "${COLOR_BLUE}Testing...${COLOR_RESET}"
python3 -u test/run_tests.py -f