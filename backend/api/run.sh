#!/bin/bash

if [ "$1" == "-h" ] || [ "$1" == "--help" ];
then
    echo "Runs the app. Default port is 5000 but different port can be passed as a first argument."
    exit
fi

source ../cmsenv
CMD="PYTHONPATH=$(cd ../; pwd)/.python_packages python3 app.py $1"
eval $CMD;
