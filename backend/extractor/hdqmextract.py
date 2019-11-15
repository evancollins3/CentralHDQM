#!/usr/bin/env python
from __future__ import print_function

from glob import glob
from multiprocessing import Pool
from collections import defaultdict
from configparser import ConfigParser
from tempfile import NamedTemporaryFile
from sqlalchemy.exc import IntegrityError

import re
import ROOT
import argparse

import metrics
from metrics import fits
from metrics import basic

import os, sys
# Insert parent dir to sys.path to import db_access
sys.path.insert(1, os.path.realpath(os.path.pardir))
import db_access

CFGFILES = 'cfg/*/*.ini'
# CFGFILES = 'cfg/Tracker/trendPlotsTracking.ini'
ROOTFILES = '/eos/cms/store/group/comm_dqm/DQMGUI_data/*/*/*/DQM*.root'
# ROOTFILES = '/afs/cern.ch/work/a/akirilov/HDQM/CentralHDQM/CentralHDQM/backend/extractor/testData/DQM*.root'
# ROOTFILES = '/eos/cms/store/group/comm_dqm/DQMGUI_data/Run2018/StreamExpress/R0003152xx/DQM_V0006*.root'

PDPATTERN = re.compile('DQM_V\d+_R\d+__(.+__.+__.+)[.]root') # PD inside the file name
VERSIONPATTERN = re.compile('(DQM_V)(\d+)(.+[.]root)')
RUNPATTERN = re.compile('DQM_V\d+_R0+(\d+)__.+[.]root')
PLOTNAMEPATTERN = re.compile('^(\w+-*\+*)+$')
DQMGUI = 'https://cmsweb.cern.ch/dqm/offline/'


def get_full_path(relativePath, run):
  parts = relativePath.split('/')
  return str('DQMData/Run %s/%s/Run summary/%s' % (run, parts[0], '/'.join(parts[1:])))


def batch_iterable(iterable, chunksize=100):
  queue=[]
  for value in iterable:
    if len(queue) >= chunksize:
      yield queue
      queue = []
    queue.append(value)
  yield queue


def remove_old_versions(all_files):
  # groups is a map: filename with version part removed -> list of all files 
  # with the same name but different version.
  groups = defaultdict(list)
  for fullpath in all_files:
    filename = fullpath.split('/')[-1]
    version = 1
    mapKey = filename
    versionMatch = VERSIONPATTERN.findall(filename)
    # We should get 3 parts: DQM_V, version and the rest of the file name
    if len(versionMatch) == 1 and len(versionMatch[0]) == 3:
      version = int(versionMatch[0][1])
      # Key is everything appart from version
      mapKey = versionMatch[0][0] + versionMatch[0][2]
  
    obj = {}
    obj['fullpath'] = fullpath
    obj['filename'] = filename
    obj['version'] = version
    
    groups[mapKey].append(obj)

  # Sort every group by version and select the latest one
  files = map(lambda x: sorted(groups[x], key=lambda elem: elem['version'], reverse=True)[0]['fullpath'], groups)
  
  return files


# Write an me to a tempfile and read binary from it.
# This is to keep the compatibility with future ROOT versions.
def get_binary(me):
  with NamedTemporaryFile() as temp_file:
    result_file = ROOT.TFile(temp_file.name, 'recreate')
    me.Write()
    result_file.Close()
    with open(temp_file.name, "rb") as file:
      return file.read()

def get_all_available_runs():
  eos_files = glob(ROOTFILES)
  runs = set()
  for filepath in eos_files:
    file = filepath.split('/')[-1]
    run_match = RUNPATTERN.findall(file)
    if not len(run_match) == 0:
      run = run_match[0]
      runs.add(int(run))
  return list(runs)


def extract_all_mes(cfg_files, runs):
  print('Processing %d configuration files...' % len(cfg_files))
  mes_set = set()
  good_files = 0
  for cfg_file in cfg_files:
    try:
      parser = ConfigParser()
      parser.read(unicode(cfg_file))
      for section in parser:
        if not section.startswith('plot:'):
          if(section != 'DEFAULT'):
            print('Invalid configuration section: %s:%s, skipping.' % (cfg_file, section))
          continue
        if not PLOTNAMEPATTERN.match(section.lstrip('plot:')):
          print("Invalid plot name: '%s:%s' Plot names can contain only alphanumeric characters or [_, +, -]" % (cfg_file, section.lstrip('plot:')))
          continue

        mes_set.add(parser[section]['relativePath'])
        if 'histo1Path' in parser[section]:
          mes_set.add(parser[section]['histo1Path'])
        if 'histo2Path' in parser[section]:
          mes_set.add(parser[section]['histo2Path'])
      good_files+=1
    except:
      print('Could not read %s, skipping...' % cfg_file)
  
  print('Read %d configuration files.' % good_files)
  print('Read %d distinct ME paths.' % len(mes_set))
  
  print('Listing files on EOS, this can take a while...')
  all_files = glob(ROOTFILES)
  print('Done.')

  # Filter on the runs that were passed by the user
  if runs:
    filtered = []
    for file in all_files:
      run_match = RUNPATTERN.findall(file)
      if not len(run_match) == 0:
        run = run_match[0]
        if(int(run) in runs):
          filtered.append(file)
    all_files = filtered

  # Keep only the newest version of each file
  print('Removing old versions of files...')
  all_files = remove_old_versions(all_files)

  print('Found %s files in EOS' % len(all_files))

  print('Setting up a temporary DB tables to find out missing MEs...')

  # Fill temp tables!
  db_access.setup_db()
  created = create_and_populate_temp_tables(mes_set, all_files)
  if not created:
    print('Unable to create temporary DB tables. Terminating.')
    return

  print('Done.')
  print('Extracting missing MEs...')

  # Join in the DB to get root file and me path pairs
  # that still don't exist in the DB
  sql = '''
  SELECT me_path, eos_path
  FROM temp_root_filenames, temp_me_paths

  WHERE NOT EXISTS (SELECT me_path, eos_path FROM processed_monitor_elements 
        WHERE temp_me_paths.me_path = processed_monitor_elements.me_path
        AND temp_root_filenames.eos_path = processed_monitor_elements.eos_path)
  LIMIT 100000
  ;
  '''

  pool = Pool(50)

  while True:
    try:
      db_access.dispose_engine()

      print('Vacuuming processed_monitor_elements table...')
      db_access.vacuum_processed_mes()

      print('Fetching not processed MEs from DB...')
      session = db_access.get_session()
      rows = session.execute(sql)
      rows = list(rows)
      session.close()
      print('Fetched.')
      if(len(rows) == 0):
        break
      
      pool.map(extract_mes, batch_iterable(rows, chunksize=2000))
    except Exception as e:
      print(e)
      session.close()
      break

  print('Done.')


def extract_mes(rows):
  tdirectory = None
  last_eos_path = None

  for row in rows:
    eos_path = row['eos_path']
    me_path = row['me_path']
    
    pd_match = PDPATTERN.findall(eos_path)
    if len(pd_match) == 0:
      dataset = ''
    else:
      dataset = '/' + pd_match[0].replace('__', '/')

    filename = eos_path.split('/')[-1]
    run_match = RUNPATTERN.findall(filename)
    if not len(run_match) == 0:
      run = run_match[0]
    else:
      print('Skipping a malformatted DQM file that does not contain a run number: %s' % eos_path)
      insert_non_existent_me_to_db(eos_path, me_path)
      continue
    
    # Open root file only if it's different from the last one
    if eos_path != last_eos_path or tdirectory == None:
      if tdirectory != None:
        tdirectory.Close()
      tdirectory = ROOT.TFile.Open(eos_path)
      last_eos_path = eos_path

    if tdirectory == None:
      print("Unable to open file: '%s'" % eos_path)
      insert_non_existent_me_to_db(eos_path, me_path)
      continue

    fullpath = get_full_path(me_path, run)
    plot = tdirectory.Get(fullpath)
    if not plot:
      insert_non_existent_me_to_db(eos_path, me_path)
      continue

    plot_folder = '/'.join(me_path.split('/')[:-1])
    gui_url = '%sstart?runnr=%s;dataset=%s;workspace=Everything;root=%s;focus=%s;zoom=yes;' % (DQMGUI, run, dataset, plot_folder, me_path)
    image_url = '%splotfairy/archive/%s%s/%s?v=1510330581101995531;w=1906;h=933' % (DQMGUI, run, dataset, me_path)
    monitor_element = db_access.MonitorElement(
          run = run,
          lumi = 0,
          eos_path = eos_path,
          me_path = me_path,
          dataset = dataset,
          me_blob = get_binary(plot),
          gui_url = gui_url,
          image_url = image_url)
    insert_me_to_db(monitor_element)

  if tdirectory != None:
    tdirectory.Close()


# Insert non existent ME.
# Next time we will no longer try to fetch this ME.
def insert_non_existent_me_to_db(eos_path, me_path):
  processed_monitor_element = db_access.ProcessedMonitorElement(
    eos_path = eos_path,
    me_path = me_path,
    me_id = None
  )

  session = db_access.get_session()
  try:
    session.add(processed_monitor_element)
    session.commit()
    print('Added non existent ME to DB')
  except Exception as e:
    print('Insert non existent ME error: %s' % e)
    session.rollback()
  finally:
    session.close()


def insert_me_to_db(monitor_element):
  session = db_access.get_session()
  try:
    session.add(monitor_element)
    session.flush()

    # Add ME to the list of processed MEs
    processed_monitor_element = db_access.ProcessedMonitorElement(
      eos_path = monitor_element.eos_path,
      me_path = monitor_element.me_path,
      me_id = monitor_element.id
    )
    session.add(processed_monitor_element)

    session.commit()
    print('Added ME to DB: %s', monitor_element.id)
  except Exception as e:
    print('Insert ME error: %s' % e)
    session.rollback()
  finally:
    session.close()


# Store all currently present EOS files and MEs from .ini files 
# in temporary DB tables.
# We will join them later to reduce the query size.
# The result will be joined with main MEs table to get only missing 
# file, me pairs to extract.
def create_and_populate_temp_tables(mes_set, all_files):
  # Drop temp tables
  sql_drop_temp_filenames = '''
  DROP TABLE IF EXISTS temp_root_filenames;
  '''
  sql_drop_temp_me_paths = '''
  DROP TABLE IF EXISTS temp_me_paths;
  '''

  # Create temp tables
  sql_create_temp_filenames = '''
  CREATE TABLE temp_root_filenames (
    eos_path character varying NOT NULL
  );
  '''
  sql_create_temp_me_paths = '''
  CREATE TABLE temp_me_paths (
    me_path character varying NOT NULL
  );
  '''

  sql_insert_paths = '''INSERT INTO temp_root_filenames (eos_path) VALUES (:eos_path);'''
  sql_insert_mes = '''INSERT INTO temp_me_paths (me_path) VALUES (:me_path);'''

  # Populate temp table of eos paths
  # sql_insert_paths_query_params = {}
  # sql_insert_paths_keys = ''

  # for i, filepath in enumerate(all_files):
  #   key = 'eos_path_%s' % i
  #   sql_insert_paths_keys += '(:%s),' % key
  #   sql_insert_paths_query_params[key] = filepath
  # sql_insert_paths_keys = sql_insert_paths_keys.rstrip(',')

  # sql_insert_paths = '''
  # INSERT INTO temp_root_filenames (eos_path)
  # VALUES
  # %s
  # ;
  # ''' % sql_insert_paths_keys

  # # Populate temp table of ME paths
  # sql_insert_mes_query_params = {}
  # sql_insert_mes_keys = ''
  # for i, me_path in enumerate(mes_set):
  #   key = 'me_path_%s' % i
  #   sql_insert_mes_keys += '(:%s),' % key
  #   sql_insert_mes_query_params[key] = me_path
  # sql_insert_mes_keys = sql_insert_mes_keys.rstrip(',')

  # sql_insert_mes = '''
  # INSERT INTO temp_me_paths (me_path)
  # VALUES
  # %s
  # ;
  # ''' % sql_insert_mes_keys

  session = db_access.get_session()
  try:
    session.execute(sql_drop_temp_filenames)
    session.execute(sql_drop_temp_me_paths)
    session.execute(sql_create_temp_filenames)
    session.execute(sql_create_temp_me_paths)
    session.execute(sql_insert_paths, [{'eos_path': x} for x in all_files])
    session.execute(sql_insert_mes, [{'me_path': x} for x in mes_set])
    session.commit()
  except Exception as e:
    print(e)
    return False
  finally:
    session.close()
  
  return True

def test(rows):
  print(len(rows))

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
  
  extract_all_mes(config, runs)

  # exit()
  # Get last 101
  # print(sorted(list(get_all_available_runs()))[-101:])
  # parser = argparse.ArgumentParser(description='HDQM monitor element extractor.')
  # parser.add_argument('-r', dest='runs', type=int, nargs='+', help='Runs to process. If none were given, will process all available runs.')
  # args = parser.parse_args()

  # if args.runs == None:
  #   runs = get_all_available_runs()
  # else:
  #   runs = args.runs

  # pool = Pool(50)
  # runs = [322169, 296365, 318734, 318735, 306528, 306529, 318733, 306522, 306523, 306520, 306521, 306526, 306527, 301062, 301063, 301060, 301061, 301067, 301064, 304013, 301068, 304018, 300256, 300257, 300255, 300259, 323277, 323270, 323279, 297705, 322902, 297702, 297701, 325306, 325309, 325308, 298069, 322909, 295851, 295854, 297563, 297562, 298393, 298392, 298397, 298398, 316991, 305764, 305766, 305761]
  # runs = [322169, 296365]
  # runs = [296365]
  # runs = [319654, 319656, 319657, 319658, 319659, 319661, 319663, 319666, 319667, 319670, 319672, 319675, 319678, 319680, 319682, 319683, 319685, 319686, 319687, 319688, 319689, 319690]
  # runs = [319690]
  # runs = [325449, 325458, 325460, 325461, 325463, 325464, 325465, 325466, 325467, 325469, 325470, 325473, 325476, 325477, 325484, 325486, 325492, 325493, 325494, 325495, 325496, 325497, 325500, 325501, 325503, 325506, 325511, 325517, 325518, 325519, 325520, 325522, 325523, 325524, 325525, 325526, 325529, 325530, 325531, 325543, 325550, 325552, 325553, 325554, 325556, 325562, 325565, 325574, 325575, 325577, 325578, 325587, 325588, 325589, 325590, 325591, 325593, 325594, 325597, 325604, 325605, 325606, 325607, 325615, 325616, 325617, 325618, 325619, 325620, 325621, 325622, 325627, 325631, 325637, 325639, 325642, 325643, 325644, 325645, 325646, 325647, 325648, 325653, 325654, 325657, 325680, 325681, 325682, 325684, 325688, 325695, 325696, 325697, 325698, 325699, 325700, 325701, 325702, 325743, 325746]
  # runs = [325449]
  # runs = runs[-1000:-1]
  # runs = [r for r in runs if r > 324418 and r < 325310]
  # print(runs)
  # runs = [325449]
  # pool.map(process_run, runs)
