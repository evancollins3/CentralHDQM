#!/bin/bash
# A script to generate collections.json content for plot files in a given directory

if [ -z $1 ]; then dir="."; else dir=$1; fi

ls -l $dir | awk '{print "{" "\n" "\t" "\"files\" : [" "\n" "\t" "\t" "\"" $9 "\"" "\n" "\t" "]," "\n" "\t" "\"name\" : " "\"" $9 "\"" "," "\n" "\t" "\"corr\" : false" "\n" "},"}' | sed 's/.json//g'

