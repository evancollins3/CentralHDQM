#!/usr/bin/env python
from __future__ import print_function

from sys import argv
from glob import glob
from multiprocessing import Pool
from collections import defaultdict
from configparser import ConfigParser
from tempfile import NamedTemporaryFile
from sqlalchemy.exc import IntegrityError

import re
# import ROOT
import tempfile
import argparse

import metrics
from metrics import fits
from metrics import basic

import os, sys
# Insert parent dir to sys.path to import db_access
sys.path.insert(1, os.path.realpath(os.path.pardir))
import db_access

CFGFILES = 'cfg/*/*.ini'

def calculate_trends(cfg_files, runs):
  config_parsers = []
  good_files = 0
  for cfg_file in cfg_files:
    try:
      subsystem = os.path.basename(os.path.dirname(cfg_file))
      if not subsystem:
        subsystem = 'Unknown'
      parser = ConfigParser()
      parser.read(unicode(cfg_file))
      config_parsers.append({'parser': parser, 'subsystem': subsystem})
      good_files += 1
    except:
      print('Could not read %s, skipping...' % cfg_file)
  print('Read %d configuration files.' % good_files)

  




if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='HDQM trend calculation.')
  parser.add_argument('-r', dest='runs', type=int, nargs='+', help='Runs to process. If none were given, will process all available runs.')
  parser.add_argument('-c', dest='config', nargs='+', help='Configuration files to process. If none were given, will process all available configuration files. Files must come from here: cfg/*/*.ini')
  args = parser.parse_args()

  runs = args.runs
  config = args.config

  if config == None:
    config = glob(CFGFILES)

  # Validate config files
  for cfg_file in config:
    if cfg_file.count('/') != 2 or not cfg_file.startswith('cfg/'):
      print('Invalid configuration file: %s' % cfg_file)
      print('Configuration files must come from here: cfg/*/*.ini')
      exit()

  calculate_trends(config, runs)
