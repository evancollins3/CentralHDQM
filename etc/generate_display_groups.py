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

PLOTNAMEPATTERN = re.compile('^[a-zA-Z0-9_+-]*$')
CFGFILES = '../backend/extractor/cfg/*/*.ini'


def generate():
  # Read configs
  cfg_files = glob(CFGFILES)
  configs = []

  for cfg_file in cfg_files:
    subsystem = os.path.basename(os.path.dirname(cfg_file))
    if not subsystem:
      subsystem = 'Unknown'

    parser = RawConfigParser()
    parser.read(unicode(cfg_file))

    for section in parser:
      if not section.startswith('plot:'):
        if(section != 'DEFAULT'):
          print('Invalid configuration section: %s:%s, skipping.' % (cfg_file, section))
        continue

      if not PLOTNAMEPATTERN.match(section.lstrip('plot:')):
        print("Invalid plot name: '%s:%s' Plot names can contain only: [a-zA-Z0-9_+-]" % (cfg_file, section.lstrip('plot:')))
        continue

      if 'metric' not in parser[section] or\
         'relativePath' not in parser[section] or\
         'yTitle' not in parser[section]:
        print('Plot missing required attributes: %s:%s, skipping.' % (cfg_file, section))
        print('Required parameters: metric, relativePath, yTitle')
        continue
      
      parser[section]['subsystem'] = subsystem
      parser[section]['name'] = section.split(':')[1]
      configs.append(parser[section])

  # Generate
  with open('/data/hdqm/data/collections.json') as json_file:
    data = json.load(json_file)
    last_subsystem = None
    for config in configs:
      old_config = next((x for x in data if x['name'] == config['name']), None)

      if old_config and len(old_config['files']) > 1:
        plot_title = config.get('plotTitle')
        if not plot_title:
          plot_title = config['yTitle']

        if config['subsystem'] != last_subsystem:
          last_subsystem = config['subsystem']
          print('')
          print('\t\t// ======================================== %s ========================================' % config['subsystem'])

        print('\t\t{')
        print('\t\t\tname: "%s%s",' % (config['name'], '_group'))
        print('\t\t\tplot_title: "%s",' % plot_title)
        print('\t\t\ty_title: "%s",' % config['yTitle'])
        print('\t\t\tsubsystem: "%s",' % config['subsystem'])
        print('\t\t\tcorrelation: %s,' % str(old_config['corr']).lower())
        print('\t\t\tseries: [%s],' % ', '.join(['"%s"' % x for x in old_config['files']]))
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
