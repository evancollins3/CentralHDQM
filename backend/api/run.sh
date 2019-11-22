#!/bin/bash

if [ "$1" == "-h" ] || [ "$1" == "--help" ];
then
    echo "Runs the app. If -d is added, app will launch in debug mode."
    exit
fi

for arg; do
    case $arg in
        -d)
        DEBUG="-d"
        ;;
    esac
done

source ../cmsenv
CMD="PYTHONPATH=$(cd ../; pwd)/.python_packages python3 app.py $DEBUG"
eval $CMD;
