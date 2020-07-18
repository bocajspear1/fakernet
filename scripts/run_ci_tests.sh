#!/bin/bash

python3 -m venv ./venv
source ./venv/bin/activate
pip3 install -r requirements.txt

python3 tools/full-clean.py -f
python3 tools/clean-images.py -f
python3 build.py
python3 test/test_all.py -f