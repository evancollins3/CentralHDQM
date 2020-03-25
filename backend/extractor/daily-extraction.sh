#!/bin/bash

# This is executed by the systemd timer every day.
# This script extracts new data from EOS and populates the HDQM database
# so no manual extraction has to be done.

# Authenticate to EOS
kinit -kt /data/hdqm/.keytab cmsdqm
/usr/bin/eosfusebind -g

source ../cmsenv

# Extract
export PYTHONPATH="$(cd ../; pwd)/.python_packages/python2"
./hdqmextract.py
./calculate.py

# Collect OMS and RR info about runs
export PYTHONPATH="$(cd ../; pwd)/.python_packages/python3"
./oms_extractor.py
./rr_extractor.py

# Prewarm the datbase for normal usage
./db_prewarm.py

echo "Extraction finished."
