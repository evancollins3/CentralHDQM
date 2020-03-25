#!/usr/bin/env python
from __future__ import print_function

from sys import argv
from glob import glob
from collections import defaultdict
from configparser import RawConfigParser

import re
import os
import math
import json
import errno
import tempfile
import argparse

CFGFILES = '../backend/extractor/cfg/*/*.ini'

def generate():
  # Read configs
  cfg_files = glob(CFGFILES)
  parser = RawConfigParser()

  for cfg_file in cfg_files:
    subsystem = os.path.basename(os.path.dirname(cfg_file))
    if not subsystem:
      subsystem = 'Unknown'
    
    inner_parser = RawConfigParser()
    inner_parser.read(unicode(cfg_file))
    for section in inner_parser.sections():
      parser[section] = inner_parser[section]
      parser[section]['subsystem'] = subsystem

  # Generate JS configuration
  with open('/afs/cern.ch/user/b/battilan/public/forAndrius/collections_2017.json') as json_file:
    data = json.load(json_file)

    # Filter out non Muon keys
    keys = [x for x in data.keys() if 'muon' in x.lower()]

    parser_keys = parser.keys()
    parser_keys_lower = [k.lower() for k in parser.keys()]

    for key in keys:
      for config in data[key]:
        if len(config['files']) > 1:
          section_title = ('plot:%s' % config['files'][0]).lower()
          if section_title in parser_keys_lower:
            # ConfigParser is case sensitive so we have to arrays.
            # In first one we search and we use the value of the original
            # section to get it
            key_index = parser_keys_lower.index(section_title)
            original_key = parser_keys[key_index]
            section = parser[original_key]

            print('\t\t{')
            print('\t\t\tname: "%s",' % config['name'])
            print('\t\t\tplot_title: "%s",' % config['name'])
            print('\t\t\ty_title: "%s",' % section['yTitle'])
            print('\t\t\tsubsystem: "%s",' % section['subsystem'])
            print('\t\t\tcorrelation: %s,' % str(config['corr']).lower())
            print('\t\t\tseries: [%s],' % ', '.join(['"%s"' % x for x in config['files']]))
            print('\t\t},')

if __name__ == '__main__':
  generate()

# Sample display config:
# { 
#   name: "SomeNameLikeID",
#   plot_title: "Fancy plot name 1",
#   y_title: "Some title",
#   subsystem: "Tracker",
#   correlation: false,
#   series: ["NumberOfALCARecoTracks", "NumberOfTrack_mean", "NumberofPVertices_mean"]
# },
