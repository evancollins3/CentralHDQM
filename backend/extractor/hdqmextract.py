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

CFGFILES = 'cfg/*/*.ini'
# CFGFILES = 'cfg/Tracker/trendPlotsTracking.ini'
ROOTFILES = '/eos/cms/store/group/comm_dqm/DQMGUI_data/*/*/*/DQM*.root'
# ROOTFILES = '/afs/cern.ch/work/a/akirilov/HDQM/CentralHDQM/CentralHDQM/backend/extractor/testData/DQM*.root'
# ROOTFILES = '/eos/cms/store/group/comm_dqm/DQMGUI_data/Run2018/StreamExpress/R0003152xx/DQM_V0006*.root'

PDPATTERN = re.compile('DQM_V\d+_R\d+__(.+__.+__.+)[.]root') # PD inside the file name
VERSIONPATTERN = re.compile('(DQM_V)(\d+)(.+[.]root)')
RUNPATTERN = re.compile('DQM_V\d+_R0+(\d+)__.+[.]root')
DQMGUI = 'https://cmsweb.cern.ch/dqm/offline/'

def process_run(run):
  cfg_files = glob(CFGFILES)
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

  print('Listing files on EOS, this can take a while...')
  eos_files = glob(ROOTFILES)
  print('Done.')

  all_files = []
  rungroup = '_R%09d_' % run
  files = [file for file in eos_files if rungroup in file]
  all_files += files

  # Keep only the newest version of each file
  all_files = remove_old_versions(all_files)

  print('About to process %s files...' % len(all_files))

  result = []
  for filename in all_files:
    pd_match = PDPATTERN.findall(filename)
    if len(pd_match) == 0:
      dataset = ''
      pd = ''
    else:
      dataset = '/' + pd_match[0].replace('__', '/')
      pd = pd_match[0].split('__')[0]
    
    tdirectory = ROOT.TFile.Open(filename)
    if tdirectory == None:
      print("Unable to open file: '%s'" % filename)
      continue

    for folder in tdirectory.Get('DQMData').GetListOfKeys():
      if not folder.GetTitle().startswith('Run '):
        continue
      run = int(folder.GetTitle().split(' ')[1])

      for parser in config_parsers:
        for section in parser['parser']:
          if not section.startswith("plot:"):
            continue

          me_path = parser['parser'][section]['relativePath']
          plot_folder = '/'.join(parser['parser'][section]['relativePath'].split('/')[:-1])
          gui_url = '%sstart?runnr=%s;dataset=%s;workspace=Everything;root=%s;focus=%s;zoom=yes;' % (DQMGUI, run, dataset, plot_folder, me_path)
          image_url = '%splotfairy/archive/%s%s/%s?v=1510330581101995531;w=1906;h=933' % (DQMGUI, run, dataset, me_path)
          
          try:
            (value, histo, optional_me1, optional_me2) = extract_metric(tdirectory, parser['parser'][section], run)
            obj = {}
            obj['run'] = run
            obj['lumi'] = 0
            obj['subsystem'] = parser['subsystem']
            obj['name'] = section.split(':')[1]
            obj['dataset'] = dataset
            obj['pd'] = pd
            obj['y_title'] = parser['parser'][section]['yTitle']
            obj['value'] = value[0]
            obj['error'] = value[1]

            if 'plotTitle' in parser['parser'][section]:
              obj['plot_title'] = parser['parser'][section]['plotTitle']
            else:
              obj['plot_title'] = section.strip('plot:')
            
            obj['eos_path'] = filename
            obj['me_path'] = me_path
            obj['gui_url'] = gui_url
            obj['image_url'] = image_url

            obj['me_blob'] = get_binary(histo)
            if optional_me1:
              obj['optional_me1_blob'] = get_binary(optional_me1)
              obj['optional_me1_path'] = parser['parser'][section]['histo1Path']
            if optional_me2:
              obj['optional_me2_blob'] = get_binary(optional_me2)
              obj['optional_me2_path'] = parser['parser'][section]['histo2Path']

            result.append(obj)
          except Exception as e:
            print(e)

    tdirectory.Close()
  
  print('Done.')
  print('Writing to a database...')

  db_access.setup_db()

  for obj in result:
    historic_data = db_access.HistoricData(
      run = obj['run'],
      lumi = obj['lumi'],
      subsystem = obj['subsystem'],
      name = obj['name'],
      dataset = obj['dataset'],
      pd = obj['pd'],
      y_title = obj['y_title'],
      plot_title = obj['plot_title'],
      value = obj['value'],
      error = obj['error'],
    )

    def make_me_object(me_binary, me_path):
      return db_access.MonitorElement(
        run = obj['run'],
        lumi = obj['lumi'],
        eos_path = obj['eos_path'],
        me_path = me_path,
        dataset = obj['dataset'],
        me_blob = me_binary,
        gui_url = obj['gui_url'],
        image_url = obj['image_url'],
      )

    main_me = make_me_object(obj['me_blob'], obj['me_path'])
    session = db_access.get_session()
    historic_data.main_me_id = insert_me_to_db_old(session, main_me)

    if 'optional_me1_blob' in obj:
      optional_me1 = make_me_object(obj['optional_me1_blob'], obj['optional_me1_path'])
      session = db_access.get_session()
      historic_data.optional_me1_id = insert_me_to_db_old(session, optional_me1)

    if 'optional_me2_blob' in obj:
      optional_me2 = make_me_object(obj['optional_me2_blob'], obj['optional_me2_path'])
      session = db_access.get_session()
      historic_data.optional_me2_id = insert_me_to_db_old(session, optional_me2)

    session = db_access.get_session()
    insert_historic_data_to_db(session, historic_data)
  
  print('Done.')

def extract_metric(tdirectory, section, run):
  metric = eval(section['metric'], {'fits': fits, 'basic': basic})

  if 'threshold' in section:
    metric.setThreshold(section['threshold'])

  histo = None
  optional_me1 = None
  optional_me2 = None

  if 'histo1Path' in section:
    optional_me1 = tdirectory.Get(get_full_path(section['histo1Path'], run))
    if not optional_me1:
      raise Exception("Unable to get histo1Path '%s' from file %s'" % (section['histo1Path'], tdirectory.GetName()))
    metric.setOptionalHisto1(optional_me1)
  if 'histo2Path' in section:
    optional_me2 = tdirectory.Get(get_full_path(section['histo2Path'], run))
    if not optional_me2:
      raise Exception("Unable to get histo2Path '%s' from file %s'" % (section['histo2Path'], tdirectory.GetName()))
    metric.setOptionalHisto2(optional_me2)

  fullpath = get_full_path(section['relativePath'], run)
  histo = tdirectory.Get(fullpath)
  if not histo:
    raise Exception("Unable to get relativePath '%s' from file %s'" % (section['relativePath'], tdirectory.GetName()))
  value = metric.calculate(histo)
  return (value, histo, optional_me1, optional_me2)

def get_full_path(relativePath, run):
  parts = relativePath.split('/')
  return str('DQMData/Run %s/%s/Run summary/%s' % (run, parts[0], '/'.join(parts[1:])))

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

# Adds an ME object to a DB and returns its id.
# If it already exists, returns the id of an existing record.
def insert_me_to_db_old(session, me_object):
  try:
    session.add(me_object)
    session.commit()
    return me_object.id
  except IntegrityError as e:
    print('Insert ME error: %s' % e)
    session.rollback()
    me = session.query(db_access.MonitorElement).filter(
      db_access.MonitorElement.run == me_object.run,
      db_access.MonitorElement.lumi == me_object.lumi,
      db_access.MonitorElement.me_path == me_object.me_path,
      db_access.MonitorElement.dataset == me_object.dataset,
      ).one()
    return me.id
  finally:
    session.close()
  return 0

def insert_historic_data_to_db(session, historic_data_object):
  try:
    session.add(historic_data_object)
    session.commit()
  except IntegrityError as e:
    print('Insert HistoricData error: %s' % e)
    session.rollback()
    # Find existing and update non unique fields
    historic_data = session.query(db_access.HistoricData).filter(
      db_access.HistoricData.run == historic_data_object.run,
      db_access.HistoricData.lumi == historic_data_object.lumi,
      db_access.HistoricData.subsystem == historic_data_object.subsystem,
      db_access.HistoricData.name == historic_data_object.name,
      ).one()

    if historic_data is not None:
      historic_data.dataset = historic_data_object.dataset
      historic_data.pd = historic_data_object.pd
      historic_data.y_title = historic_data_object.y_title
      historic_data.plot_title = historic_data_object.plot_title
      historic_data.value = historic_data_object.value
      historic_data.error = historic_data_object.error
      session.commit()
  finally:
    session.close()

# Write an me to a tempfile and read binary from it.
# This is to keep the compatibility with future ROOT versions.
def get_binary(me):
  with tempfile.NamedTemporaryFile() as temp_file:
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


def extract_all_mes():
  cfg_files = glob(CFGFILES)
  mes_set = set()
  good_files = 0
  for cfg_file in cfg_files:
    try:
      parser = ConfigParser()
      parser.read(unicode(cfg_file))
      for section in parser:
        if section.startswith("plot:"):
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

  # Keep only the newest version of each file
  print('Removing old versions of files...')
  all_files = remove_old_versions(all_files)

  print('Found %s files in EOS' % len(all_files))

  print('Setting up a temporary DB table to find out missing MEs...')

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

  WHERE (SELECT COUNT(*) FROM monitor_elements 
        WHERE temp_me_paths.me_path = monitor_elements.me_path
        AND temp_root_filenames.eos_path = monitor_elements.eos_path
        LIMIT 1) = 0
        
  AND (SELECT COUNT(*) FROM non_existent_monitor_elements 
        WHERE temp_me_paths.me_path = non_existent_monitor_elements.me_path
        AND temp_root_filenames.eos_path = non_existent_monitor_elements.eos_path
        LIMIT 1) = 0
  LIMIT 100000
  ;
  '''

  # def iterate_db():
  #   while True:
  #     try:
  #       print('Fetching from DB...')
  #       session = db_access.get_session()
  #       rows = session.execute(sql)
  #       rows = list(rows)
  #       session.close()
  #       print('Fetched.')
  #       if(len(rows) == 0):
  #         break
  #       yield rows
  #     except Exception as e:
  #       print(e)
  #       session.close()
  #       break

    # try:
    #   session = db_access.get_session()
    #   while True:
    #     rows = session.execute(sql)
    #     rows = list(rows)
    #     if(len(rows) == 0):
    #       break
    #     yield rows
    # except Exception as e:
    #   print(e)
    # finally:
    #   session.close()

  pool = Pool(50)

  while True:
    try:
      print('Fetching from DB...')
      db_access.dispose_engine()
      session = db_access.get_session()
      rows = session.execute(sql)
      rows = list(rows)
      session.close()
      print('Fetched.')
      if(len(rows) == 0):
        break
      
      pool.map(extract_mes, batch_iterable(rows, chunksize=100))
    except Exception as e:
      print(e)
      session.close()
      break



  # for rows in iterate_db():
  #   pool.map(extract_mes, batch_iterable(rows, chunksize=100))






  # while True:
  # try:
  #   session = db_access.get_session()
  #   rows = session.execute(sql)

  #   print(rows)
  #   print(len(list(rows)))
  #   if(len(list(rows)) == 0):
  #     break

  #   print('Done.')
  #   print('Starting to extract missing MEs...')

  #   pool = Pool(50)
  #   pool.map(extract_mes, batch_iterable(rows, chunksize=100))

  #   # queue = []
  #   # for batch in batch_iterable(rows, chunksize=10000):
  #   #   result = pool.imap(extract_mes, batch_iterable(batch, chunksize=100))
  #   #   queue.append(result)

  #   #   if len(queue) >= 3:
  #   #     for _ in queue[0]: pass
  #   #     queue = queue[1:]
    
  #   # for items in queue:
  #   #   for _ in items: 
  #   #     pass

  # except Exception as e:
  #   print(e)
  # finally:
  #   session.close()

  print('Done.')


def extract_mes(rows):
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
    
    tdirectory = ROOT.TFile.Open(eos_path)
    if tdirectory == None:
      print("Unable to open file: '%s'" % eos_path)
      insert_non_existent_me_to_db(eos_path, me_path)
      continue

    fullpath = get_full_path(me_path, run)
    plot = tdirectory.Get(fullpath)
    if not plot:
      insert_non_existent_me_to_db(eos_path, me_path)
      tdirectory.Close()
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

    tdirectory.Close()

# Insert non existent ME.
# Next time we will no longer try to fetch this ME.
def insert_non_existent_me_to_db(eos_path, me_path):
  non_existent_monitor_element = db_access.NonExistentMonitorElement(
    eos_path = eos_path,
    me_path = me_path)

  session = db_access.get_session()
  try:
    session.add(non_existent_monitor_element)
    session.commit()
    print("Added non existent ME (%s, %s)" % (me_path, eos_path))
  except Exception as e:
    print('Insert non existent ME error: %s' % e)
    session.rollback()
  finally:
    session.close()


def insert_me_to_db(monitor_element):
  session = db_access.get_session()
  try:
    session.add(monitor_element)
    session.commit()
    print('Added ME to DB')
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

  # Populate temp table of eos paths
  sql_insert_paths_query_params = {}
  sql_insert_paths_keys = ''

  for i, filepath in enumerate(all_files):
    key = 'eos_path_%s' % i
    sql_insert_paths_keys += '(:%s),' % key
    sql_insert_paths_query_params[key] = filepath
  sql_insert_paths_keys = sql_insert_paths_keys.rstrip(',')

  sql_insert_paths = '''
  INSERT INTO temp_root_filenames (eos_path)
  VALUES
  %s
  ;
  ''' % sql_insert_paths_keys

  # Populate temp table of ME paths
  sql_insert_mes_query_params = {}
  sql_insert_mes_keys = ''
  for i, me_path in enumerate(mes_set):
    key = 'me_path_%s' % i
    sql_insert_mes_keys += '(:%s),' % key
    sql_insert_mes_query_params[key] = me_path
  sql_insert_mes_keys = sql_insert_mes_keys.rstrip(',')

  sql_insert_mes = '''
  INSERT INTO temp_me_paths (me_path)
  VALUES
  %s
  ;
  ''' % sql_insert_mes_keys

  session = db_access.get_session()
  try:
    session.execute(sql_drop_temp_filenames)
    session.execute(sql_drop_temp_me_paths)
    session.execute(sql_create_temp_filenames)
    session.execute(sql_create_temp_me_paths)
    session.execute(sql_insert_paths, sql_insert_paths_query_params)
    session.execute(sql_insert_mes, sql_insert_mes_query_params)
    session.commit()
  except Exception as e:
    print(e)
    return False
  finally:
    session.close()
  
  return True

def batch_iterable(iterable, chunksize=100):
  queue=[]
  for value in iterable:
    if len(queue) >= chunksize:
      yield queue
      queue = []
    queue.append(value)
  yield queue


if __name__ == '__main__':
  extract_all_mes()
  exit()
  # Get last 101
  # print(sorted(list(get_all_available_runs()))[-101:])
  parser = argparse.ArgumentParser(description='HDQM monitor element extractor.')
  parser.add_argument('-r', dest='runs', type=int, nargs='+', help='Runs to process. If none were given, will process all available runs.')
  args = parser.parse_args()

  if args.runs == None:
    runs = get_all_available_runs()
  else:
    runs = args.runs

  pool = Pool(50)
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
  runs = [325449]
  pool.map(process_run, runs)
