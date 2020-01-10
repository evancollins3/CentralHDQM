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


def cleanup():
  cfg_files = glob(CFGFILES)

  for file in cfg_files:
    parser = RawConfigParser(allow_no_value=True)
    parser.optionxform = str
    parser.read(unicode(file))

    for section in parser:
      if not section.startswith('plot:'):
        if(section != 'DEFAULT'):
          print('Invalid configuration section: %s:%s, skipping.' % (file, section))
        continue
      
      if not PLOTNAMEPATTERN.match(section.lstrip('plot:')):
        print("Invalid plot name: '%s:%s' Plot names can contain only: [a-zA-Z0-9_+-]" % (file, section.lstrip('plot:')))
        continue

      if 'metric' not in parser[section] or\
         'relativePath' not in parser[section] or\
         'yTitle' not in parser[section]:
        print('Plot missing required attributes: %s:%s, skipping.' % (file, section))
        print('Required parameters: metric, relativePath, yTitle')
        continue

      parser.remove_option(section, 'runOffset')
      parser.remove_option(section, 'relSystematic')
      parser.remove_option(section, 'absSystematic')
      parser.remove_option(section, 'yMin')
      parser.remove_option(section, 'yMax')
      parser.remove_option(section, 'yMin')
      parser.remove_option(section, 'yMin')

      if 'hTitle' in parser[section]:
        parser[section]['plotTitle'] = parser[section]['hTitle']
        parser.remove_option(section, 'hTitle')

      with open(file, 'w') as configfile:
        parser.write(configfile)


if __name__ == '__main__':
  cleanup()
