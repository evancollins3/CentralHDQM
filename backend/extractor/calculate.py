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
import math
import ROOT
import tempfile
import argparse

import metrics
from metrics import fits
from metrics import basic

import os, sys
# Insert parent dir to sys.path to import db_access
sys.path.insert(1, os.path.realpath(os.path.pardir))
import db_access
from helpers import batch_iterable, exec_transaction

PLOTNAMEPATTERN = re.compile('^[a-zA-Z0-9_+-]*$')
CFGFILES = 'cfg/*/*.ini'

# Globallist of configs will be shared between processes
CONFIG=[]


def get_optional_me(eos_path, me_path):
  sql = 'SELECT id, me_blob FROM monitor_elements WHERE eos_path=:eos_path AND me_path=:me_path;'
  session = db_access.get_session()
  try:
    me = session.execute(sql, {'eos_path': eos_path, 'me_path': me_path})
  except Exception as e:
    print(e)
  finally:
    session.close()

  if not me:
    return None, None
  return me[0]['id'], me[0]['me_blob']


# Returns a ROOT plot from binary file
def get_plot_from_blob(me_blob):
  with tempfile.NamedTemporaryFile() as temp_file:
    with open(temp_file.name, 'w+b') as fd:
      fd.write(me_blob)
    tdirectory = ROOT.TFile(temp_file.name, 'read')
    plot = tdirectory.GetListOfKeys()[0].ReadObj()
    return plot, tdirectory


def calculate_all_trends(cfg_files, runs, nprocs):
  print('Processing %d configuration files...' % len(cfg_files))
  # db_access.setup_db()
  
  trend_count=0
  # config=[]
  for cfg_file in cfg_files:
    subsystem = os.path.basename(os.path.dirname(cfg_file))
    if not subsystem:
      subsystem = 'Unknown'

    parser = ConfigParser()
    parser.read(unicode(cfg_file))

    for section in parser:
      if not section.startswith('plot:'):
        if(section != 'DEFAULT'):
          print('Invalid configuration section: %s:%s, skipping.' % (cfg_file, section))
        continue

      if not PLOTNAMEPATTERN.match(section.lstrip('plot:')):
        print("Invalid plot name: '%s:%s' Plot names can contain only: [a-zA-Z0-9_+-]" % (cfg_file, section.lstrip('plot:')))
        continue

      if 'metric' not in parser[section] and\
         'relativePath' not in parser[section] and\
         'yTitle' not in parser[section]:
        print('Plot missing required attributes: %s:%s, skipping.' % (cfg_file, section))
        print('Required parameters: metric, relativePath, yTitle')
        continue
      
      parser[section]['subsystem'] = subsystem
      parser[section]['name'] = section.split(':')[1]
      CONFIG.append(parser[section])
      trend_count+=1

  print('Starting to process %s trends.' % trend_count)

  if runs == None:
    runs_filter = ''
  else:
    runs_filter = 'WHERE monitor_elements.run IN (%s)' % ', '.join(str(x) for x in runs)

  limit = 10
  sql = '''
  SELECT monitor_elements.run, monitor_elements.lumi, monitor_elements.eos_path, monitor_elements.me_path, monitor_elements.dataset, monitor_elements.me_blob FROM monitor_elements
  JOIN queue_to_calculate ON monitor_elements.id=queue_to_calculate.me_id
  %s
  LIMIT %s;
  ''' % (runs_filter, limit)

  count = 0
  session = db_access.get_session()
  try:
    count = session.execute('SELECT COUNT(*) FROM queue_to_calculate;')
    count = list(count)
    count = count[0][0]
  except Exception as e:
    print(e)
  finally:
    session.close()

  pool = Pool(nprocs)

  for _ in range(int(math.ceil(count/limit))):
    try:
      db_access.dispose_engine()
      print('Fetching not processed data points from DB...')
      session = db_access.get_session()
      rows = session.execute(sql)
      rows = list(rows)
      session.close()
      print('Fetched.')
      if len(rows) == 0:
        break
      print(rows[:10])
      pool.map(calculate_trends, batch_iterable(rows, chunksize=2000))
    except Exception as e:
      print(e)
      session.close()
      break


def calculate_trends(rows):
  db_access.dispose_engine()

  for row in rows:
    #      id     run  lumi                                          me_path                                            dataset me_blob
    # 9993145	300812      0 CSC/CSCOfflineMonitor/PedestalNoise/hStripPedMEp22	/SingleElectron/Run2017C-09Aug2019_UL2017-v1/DQMIO	  3 KB

    # All configs referencing row['me_path']
    configs = [x for x in GLOBAL if x['relativePath'] == row['me_path']]

    for config in configs:
      tdirectories=[]
      try:
        metric = eval(configs['metric'], {'fits': fits, 'basic': basic})

        # Get optional MEs
        optional_me_sql = 'SELECT me_blob FROM monitor_elements WHERE eos_path=:eos_path AND me_path=:me_path;'

        histo1_id=None
        histo2_id=None
        reference_id=None

        if 'histo1Path' in config:
          histo1_id, histo1 = get_optional_me(row['eos_path'], config['histo1Path'])
          if not histo1:
            print('Unable to get an optional monitor element: %s:%s' % (row['eos_path'], config['histo1Path']))
            continue
          plot, tdir = get_plot_from_blob(histo1)
          tdirectories.append(tdir)
          metric.setOptionalHisto1(plot)

        if 'histo2Path' in config:
          histo2_id, histo2 = get_optional_me(row['eos_path'], config['histo2Path'])
          if not histo2:
            print('Unable to get an optional monitor element: %s:%s' % (row['eos_path'], config['histo2Path']))
            continue
          plot, tdir = get_plot_from_blob(histo2)
          tdirectories.append(tdir)
          metric.setOptionalHisto2(plot)

        if 'reference' in config:
          reference_id, reference = get_optional_me(row['eos_path'], config['reference'])
          if not reference:
            print('Unable to get an optional monitor element: %s:%s' % (row['eos_path'], config['reference']))
            continue
          plot, tdir = get_plot_from_blob(reference)
          tdirectories.append(tdir)
          metric.setReference(plot)

        if 'threshold' in config:
          metric.setThreshold(config['threshold'])

        main_plot, tdir = get_plot_from_blob(row['me_blob'])
        tdirectories.append(tdir)

        # Calculate
        value, error = metric.calculate(main_plot)

        plot_title = config['yTitle']
        if 'plotTitle' in config:
          plot_title = config['plotTitle']

        # Write results to the DB
        historic_data_point = db_access.HistoricDataPoint(
          run = row['run'],
          lumi = row['lumi'],
          subsystem = config['subsystem'],
          name = config['name'],
          dataset = row['dataset'],
          pd = row['dataset'].split('/')[1],
          y_title = config['yTitle'],
          plot_title = plot_title,
          value = value,
          error = error,
          main_me_id = row['id'],
          optional_me1_id = histo1_id,
          optional_me2_id = histo2_id,
          reference_id = reference_id
        )

        session = db_access.get_session()
        try:
          session.add(historic_data_point)
          session.commit()
        except IntegrityError as e:
          print('Insert HistoricDataPoint error: %s' % e)
          session.rollback()
          print('Updating...')
          try:
            historic_data_point_existing = session.query(db_access.HistoricDataPoint).filter(
              db_access.HistoricDataPoint.subsystem == historic_data_point.subsystem,
              db_access.HistoricDataPoint.name == historic_data_point.name,
              db_access.HistoricDataPoint.main_me_id == historic_data_point.main_me_id,
            ).one_or_none()

            if historic_data_point_existing:
              historic_data_point_existing.dataset = historic_data_point.dataset
              historic_data_point_existing.pd = historic_data_point.pd
              historic_data_point_existing.y_title = historic_data_point.y_title
              historic_data_point_existing.plot_title = historic_data_point.plot_title
              historic_data_point_existing.value = historic_data_point.value
              historic_data_point_existing.error = historic_data_point.error
              historic_data_point_existing.optional_me1_id = historic_data_point.optional_me1_id,
              historic_data_point_existing.optional_me2_id = historic_data_point.optional_me2_id,
              historic_data_point_existing.reference_id = historic_data_point.reference_id
              session.commit()
              print('Updated.')
          except Exception as e:
            print('Update HistoricDataPoint error: %s' % e)
            session.rollback()
      finally:
        # Close all open TDirectories
        for tdirectory in tdirectories:
          tdirectory.Close()


if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='HDQM trend calculation.')
  parser.add_argument('-r', dest='runs', type=int, nargs='+', help='Runs to process. If none were given, will process all available runs.')
  parser.add_argument('-c', dest='config', nargs='+', help='Configuration files to process. If none were given, will process all available configuration files. Files must come from here: cfg/*/*.ini')
  parser.add_argument('-j', dest='nprocs', type=int, default=50, help='Number of processes to use for extraction.')
  args = parser.parse_args()

  runs = args.runs
  config = args.config
  nprocs = args.nprocs

  if nprocs < 0:
    print('Number of processes must be a positive integer')
    exit()

  if config == None:
    config = glob(CFGFILES)

  # Validate config files
  for cfg_file in config:
    if cfg_file.count('/') != 2 or not cfg_file.startswith('cfg/'):
      print('Invalid configuration file: %s' % cfg_file)
      print('Configuration files must come from here: cfg/*/*.ini')
      exit()

  calculate_all_trends(config, runs, nprocs)
