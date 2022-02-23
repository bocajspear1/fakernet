#!/bin/bash

cd /opt/fakernet 
source ./venv/bin/activate 
python3 build.py 
python3 tools/full-clean.py -f
python3 tools/clean-images.py -f
python3 build.py
python3 test/test_all.py -f