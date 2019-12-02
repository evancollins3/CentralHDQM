#!/usr/bin/env python
from __future__ import print_function

from sys import argv
from glob import glob
from multiprocessing import Pool
from collections import defaultdict
from configparser import RawConfigParser
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
from helpers import batch_iterable, exec_transaction, get_all_me_names

PLOTNAMEPATTERN = re.compile('^[a-zA-Z0-9_+-]*$')
CFGFILES = 'cfg/*/*.ini'

# Globallist of configs will be shared between processes
CONFIG=[]


def get_optional_me(eos_path, me_paths):
  sql = 'SELECT id, me_blob FROM monitor_elements WHERE eos_path=:eos_path AND me_path=:me_path;'
  for me_path in me_paths:
    session = db_access.get_session()
    me=None
    try:
      me = session.execute(sql, {'eos_path': eos_path, 'me_path': me_path})
      me = list(me)
    except Exception as e:
      print(e)
    finally:
      session.close()

    if me:
      return me[0]['id'], me[0]['me_blob']

  # None were found
  return None, None


def get_me_by_id(id):
  sql = 'SELECT me_blob FROM monitor_elements WHERE id=:id;'
  session = db_access.get_session()
  me=None
  try:
    me = session.execute(sql, {'id': id})
    me = list(me)
  except Exception as e:
    print(e)
  finally:
    session.close()

  if not me:
    return None
  return me[0]['me_blob']


# def get_queue_length():
#   count = 0
#   session = db_access.get_session()
#   try:
#     count = session.execute('SELECT COUNT(*) FROM queue_to_calculate;')
#     count = list(count)
#     count = count[0][0]
#   except Exception as e:
#     print(e)
#   finally:
#     session.close()
#   return count


def move_to_second_queue(me_id, queue_id):
  session = db_access.get_session()
  try:
    session.execute('INSERT INTO queue_to_calculate_later (me_id) VALUES (:me_id);', {'me_id': me_id})
    session.execute('DELETE FROM queue_to_calculate WHERE id = :queue_id;', {'queue_id': queue_id})
    session.commit()
  except Exception as e:
    session.rollback()
    print(e)
  finally:
    session.close()


# Returns a ROOT plot from binary file
def get_plot_from_blob(me_blob):
  with tempfile.NamedTemporaryFile() as temp_file:
    with open(temp_file.name, 'w+b') as fd:
      fd.write(me_blob)
    tdirectory = ROOT.TFile(temp_file.name, 'read')
    plot = tdirectory.GetListOfKeys()[0].ReadObj()
    return plot, tdirectory


def section_to_config_object(section):
  return db_access.LastCalculatedConfig(
    subsystem = section['subsystem'],
    name = section['name'],
    metric = section['metric'],
    plot_title = section.get('plotTitle') or section['yTitle'],
    y_title = section['yTitle'],
    relative_path = section['relativePath'],
    histo1_path = section.get('histo1Path'),
    histo2_path = section.get('histo2Path'),
    reference_path = section.get('reference'),
    threshold = section.get('threshold'),
  )


def calculate_all_trends(cfg_files, runs, nprocs):
  print('Processing %d configuration files...' % len(cfg_files))
  db_access.setup_db()
  
  trend_count=0
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
      CONFIG.append(parser[section])
      trend_count+=1

  print('Starting to process %s trends.' % trend_count)
  print('Updating configuration...')

  # Find out new and changed configuration
  last_config=[]
  session = db_access.get_session()
  try:
    last_config = list(session.execute('SELECT * FROM last_calculated_configs;'))
  except Exception as e:
    print('Exception getting config from the DB: %s' % e)
    return
  finally:
    session.close()

  new_configs=[]
  changed_configs=[]

  for current in CONFIG:
    # Find by subsystem and name of trend
    last = next((x for x in last_config if current['subsystem'] == x['subsystem'] and current['name'] == x['name']), None)
    if last:
      obj = section_to_config_object(current)
      if not last['metric'] == obj.metric or\
        not last['plot_title'] == obj.plot_title or\
        not last['y_title'] == obj.y_title or\
        not last['relative_path'] == obj.relative_path or\
        not last['histo1_path'] == obj.histo1_path or\
        not last['histo2_path'] == obj.histo2_path or\
        not last['reference_path'] == obj.reference_path or\
        not last['threshold'] == int(obj.threshold):
        # Changed!
        changed_configs.append(obj)
    else:
      new_configs.append(section_to_config_object(current))

  # Update changed configs
  session = db_access.get_session()
  try:
    for changed in changed_configs:
      existing = session.query(db_access.LastCalculatedConfig).\
        filter(db_access.LastCalculatedConfig.subsystem == changed.subsystem).\
        filter(db_access.LastCalculatedConfig.name == changed.name).one_or_none()

      existing.metric = changed.metric
      existing.plot_title = changed.plot_title
      existing.y_title = changed.y_title
      existing.relative_path = changed.relative_path
      existing.histo1_path = changed.histo1_path
      existing.histo2_path = changed.histo2_path
      existing.reference_path = changed.reference_path
      existing.threshold = changed.threshold
      session.flush()

    session.commit()
  except Exception as e:
    print('Exception updating changed configs in the DB: %s' % e)
    session.rollback()
  finally:
    session.close()

  # Add new configs
  session = db_access.get_session()
  try:
    for new in new_configs:
      session.add(new)
    session.commit()
  except Exception as e:
    print('Exception adding new configs to the DB: %s' % e)
    session.rollback()
    return
  finally:
    session.close()

  # Recalculate everything if the configuration changed
  if len(new_configs) + len(changed_configs) > 0:
    print('Configuration changed, reseting the calculation queue...')
    session = db_access.get_session()
    try:
      session.execute('DELETE FROM queue_to_calculate;')
      session.execute('DELETE FROM queue_to_calculate_later;')
      session.execute('INSERT INTO queue_to_calculate (me_id) SELECT id FROM monitor_elements;')
      session.commit()
    except Exception as e:
      print('Exception reseting the calculation queue in the DB: %s' % e)
      session.rollback()
      return
    finally:
      session.close()
    print('Calculation queue is ready.')
  else:
    # Move things from queue_to_calculate_later back to queue_to_calculate
    session = db_access.get_session()
    try:
      session.execute('INSERT INTO queue_to_calculate (me_id) SELECT me_id FROM queue_to_calculate_later;')
      session.execute('DELETE FROM queue_to_calculate_later;')
      session.commit()
    except Exception as e:
      print('Exception moving items from the second calculation queue to the first: %s' % e)
      session.rollback()
    finally:
      session.close()

  # Start calculating trends
  if runs == None:
    runs_filter = ''
  else:
    runs_filter = 'WHERE monitor_elements.run IN (%s)' % ', '.join(str(x) for x in runs)

  limit = 10
  sql = '''
  SELECT queue_to_calculate.id, monitor_elements.id as me_id, monitor_elements.run, monitor_elements.lumi, monitor_elements.eos_path, monitor_elements.me_path, monitor_elements.dataset FROM monitor_elements
  JOIN queue_to_calculate ON monitor_elements.id=queue_to_calculate.me_id
  %s
  LIMIT %s;
  ''' % (runs_filter, limit)

  pool = Pool(nprocs)
  # count = get_queue_length()

  # for _ in range(max(int(math.ceil(count/limit)), 1)):
  while True:
    db_access.dispose_engine()
    session = db_access.get_session()
    try:
      print('Fetching not processed data points from DB...')
      rows = session.execute(sql)
      rows = list(rows)
      print('Fetched: %s' % len(rows))
      if len(rows) == 0:
        break

      pool.map(calculate_trends, batch_iterable(rows, chunksize=5))
      print('FINISHED CALCULATING A BATCH OF TRENDS!!!!')
    except Exception as e:
      print('Exception fetching elements from the calculation queue: %s' % e)
      session.close()
      break
    finally:
      session.close()


def calculate_trends(rows):
  db_access.dispose_engine()

  for row in rows:
    print('Calculating trend:', row['eos_path'], row['me_path'])
    # All configs referencing row['me_path'] as main me
    configs = [x for x in CONFIG if row['me_path'] in get_all_me_names(x['relativePath'])]
    
    if not configs:
      print('ME not used is any config')
      move_to_second_queue(row['me_id'], row['id'])

    for config in configs:
      tdirectories=[]

      try:
        try:
          metric = eval(config['metric'], {'fits': fits, 'basic': basic})
        except Exception as e:
          print('Unable to load the metric: %s. %s' % (config['metric'], e))
          move_to_second_queue(row['me_id'], row['id'])
          continue
        
        histo1_id=None
        histo2_id=None
        reference_id=None

        if 'histo1Path' in config:
          histo1_id, histo1 = get_optional_me(row['eos_path'], get_all_me_names(config['histo1Path']))
          if not histo1:
            print('Unable to get an optional monitor element 1: %s:%s' % (row['eos_path'], config['histo1Path']))
            move_to_second_queue(row['me_id'], row['id'])
            continue
          plot, tdir = get_plot_from_blob(histo1)
          tdirectories.append(tdir)
          metric.setOptionalHisto1(plot)

        if 'histo2Path' in config:
          histo2_id, histo2 = get_optional_me(row['eos_path'], get_all_me_names(config['histo2Path']))
          if not histo2:
            print('Unable to get an optional monitor element 2: %s:%s' % (row['eos_path'], config['histo2Path']))
            move_to_second_queue(row['me_id'], row['id'])
            continue
          plot, tdir = get_plot_from_blob(histo2)
          tdirectories.append(tdir)
          metric.setOptionalHisto2(plot)

        if 'reference' in config:
          reference_id, reference = get_optional_me(row['eos_path'], get_all_me_names(config['reference']))
          if not reference:
            print('Unable to get an optional reference monitor element: %s:%s' % (row['eos_path'], config['reference']))
            move_to_second_queue(row['me_id'], row['id'])
            continue
          plot, tdir = get_plot_from_blob(reference)
          tdirectories.append(tdir)
          metric.setReference(plot)

        if 'threshold' in config:
          metric.setThreshold(config['threshold'])

        # Get main plot blob from db
        main_me_blob = get_me_by_id(row['me_id'])

        if not main_me_blob:
          print('Unable to get me_blob %s from the DB.' % row['me_id'])
          move_to_second_queue(row['me_id'], row['id'])
          continue

        main_plot, tdir = get_plot_from_blob(main_me_blob)
        tdirectories.append(tdir)

        # Get config id
        session = db_access.get_session()
        config_id=0
        try:
          config_id = session.execute('SELECT id FROM last_calculated_configs WHERE subsystem=:subsystem AND name=:name;', {'subsystem': config['subsystem'], 'name': config['name']})
          config_id = list(config_id)
          config_id = config_id[0]['id']
        except Exception as e:
          print('Unable to get config id from the DB: %s' % e)
          move_to_second_queue(row['me_id'], row['id'])
          continue
        finally:
          session.close()

        # Calculate
        try:
          value, error = metric.calculate(main_plot)
        except Exception as e:
          print('Unable to calculate the metric: %s. %s' % (config['metric'], e))
          move_to_second_queue(row['me_id'], row['id'])
          continue

        # Write results to the DB
        historic_data_point = db_access.HistoricDataPoint(
          run = row['run'],
          lumi = row['lumi'],
          dataset = row['dataset'],
          pd = row['dataset'].split('/')[1],
          value = value,
          error = error,
          main_me_id = row['me_id'],
          optional_me1_id = histo1_id,
          optional_me2_id = histo2_id,
          reference_me_id = reference_id,
          config_id = config_id
        )

        session = db_access.get_session()
        try:
          session.add(historic_data_point)
          session.execute('DELETE FROM queue_to_calculate WHERE id=:id;', {'id': row['id']})
          session.commit()
        except IntegrityError as e:
          print('Insert HistoricDataPoint error: %s' % e)
          session.rollback()
          print('Updating...')
          try:
            historic_data_point_existing = session.query(db_access.HistoricDataPoint).filter(
              db_access.HistoricDataPoint.config_id == historic_data_point.config_id,
              db_access.HistoricDataPoint.main_me_id == historic_data_point.main_me_id,
            ).one_or_none()

            if historic_data_point_existing:
              historic_data_point_existing.run = historic_data_point.run
              historic_data_point_existing.lumi = historic_data_point.lumi
              historic_data_point_existing.dataset = historic_data_point.dataset
              historic_data_point_existing.pd = historic_data_point.pd
              historic_data_point_existing.value = historic_data_point.value
              historic_data_point_existing.error = historic_data_point.error
              historic_data_point_existing.optional_me1_id = historic_data_point.optional_me1_id,
              historic_data_point_existing.optional_me2_id = historic_data_point.optional_me2_id,
              historic_data_point_existing.reference_me_id = historic_data_point.reference_me_id
              session.commit()
              print('Updated.')
          except Exception as e:
            print('Update HistoricDataPoint error: %s' % e)
            session.rollback()
            move_to_second_queue(row['me_id'], row['id'])
        finally:
          session.close()
      except Exception as e:
        print('Exception calculating trend: %s' % e)
        move_to_second_queue(row['me_id'], row['id'])
        continue
      finally:
        # Close all open TDirectories
        for tdirectory in tdirectories:
          if tdirectory:
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
