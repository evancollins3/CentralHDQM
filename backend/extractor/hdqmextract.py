#!/usr/bin/env python
from __future__ import print_function

from sys import argv
from glob import glob
from multiprocessing import Pool
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
# CFGFILES = 'cfg/trendPlotsTrackingCosmics.ini'
# CFGFILES = 'cfg/trendPlotsPixelPhase1_DigiCluster.ini'
# CFGFILES = 'cfg/*.ini'
# CFGFILES = 'cfg/trendPlotsRECOErrorsCosmics.ini'
# CFGFILES = 'cfg/trendPlotsStrip_aleTestCharge.ini'
ROOTFILES = '/eos/cms/store/group/comm_dqm/DQMGUI_data/*/*/*/DQM*.root'
# ROOTFILES = '/afs/cern.ch/work/a/akirilov/HDQM/CentralHDQM/CentralHDQM/backend/extractor/testData/DQM*.root'
PDPATTERN = re.compile('DQM_V\d+_R\d+__(.+__.+__.+)[.]root') # PD inside the file name
VERSIONPATTERN = re.compile('(DQM_V)(\d+)(.+[.]root)')
RUNPATTERN = re.compile('DQM_V\d+_R0+(\d+)__.+[.]root')
DQMGUI = 'https://cmsweb.cern.ch/dqm/offline/'

def process_run(run):
  cfg_files = glob(CFGFILES)
  # plot_desc = ConfigParser()
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

  # Import ROOT now to fail fast
  # import ROOT

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

    for folder in tdirectory.Get('DQMData').GetListOfKeys():
      if not folder.GetTitle().startswith('Run '):
        continue
      run = int(folder.GetTitle().split(' ')[1])

      # for section in plot_desc:
      #   if not section.startswith("plot:"):
      #     continue
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
    historic_data.main_me_id = insert_me_to_db(session, main_me)

    if 'optional_me1_blob' in obj:
      optional_me1 = make_me_object(obj['optional_me1_blob'], obj['optional_me1_path'])
      session = db_access.get_session()
      historic_data.optional_me1_id = insert_me_to_db(session, optional_me1)

    if 'optional_me2_blob' in obj:
      optional_me2 = make_me_object(obj['optional_me2_blob'], obj['optional_me2_path'])
      session = db_access.get_session()
      historic_data.optional_me2_id = insert_me_to_db(session, optional_me2)

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
  groups = {}
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

    if mapKey not in groups.keys():
      groups[mapKey] = []
    
    groups[mapKey].append(obj)

  # Sort every group by version and select the latest one
  files = map(lambda x: sorted(groups[x], key=lambda elem: elem['version'], reverse=True)[0]['fullpath'], groups)
  
  return files

# Adds an ME object to a DB and returns its id.
# If it already exists, returns the id of an existing record.
def insert_me_to_db(session, me_object):
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
      db_access.HistoricData.dataset == historic_data_object.dataset,
      ).one()

    if historic_data is not None:
      historic_data.dataset = historic_data_object.dataset
      historic_data.pd = historic_data_object.pd
      historic_data.y_title = historic_data_object.y_title
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
  return runs

if __name__ == '__main__':
  # print(list(get_all_available_runs())[100:])
  parser = argparse.ArgumentParser(description='HDQM data extractor.')
  parser.add_argument('-r', dest='runs', type=int, nargs='+', help='Runs to process. If none were given, will process all available runs.')
  args = parser.parse_args()

  if args.runs == None:
    runs = get_all_available_runs()
  else:
    runs = args.runs

  pool = Pool(25)
  # runs = [322169, 296365, 318734, 318735, 306528, 306529, 318733, 306522, 306523, 306520, 306521, 306526, 306527, 301062, 301063, 301060, 301061, 301067, 301064, 304013, 301068, 304018, 300256, 300257, 300255, 300259, 323277, 323270, 323279, 297705, 322902, 297702, 297701, 325306, 325309, 325308, 298069, 322909, 295851, 295854, 297563, 297562, 298393, 298392, 298397, 298398, 316991, 305764, 305766, 305761]
  # runs = [322169, 296365]
  runs = [296365]
  pool.map(process_run, runs)
