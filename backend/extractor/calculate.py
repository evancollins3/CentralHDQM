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

def calculate_trends(cfg_files, runs):
  print('Processing %d configuration files...' % len(cfg_files))
  db_access.setup_db()
  trend_count=0
  for cfg_file in cfg_files:
    try:
      subsystem = os.path.basename(os.path.dirname(cfg_file))
      if not subsystem:
        subsystem = 'Unknown'
      parser = ConfigParser()
      parser.read(unicode(cfg_file))
      
      for section in parser:
        if not section.startswith("plot:"):
          if(section != 'DEFAULT'):
            print('Invalid configuration section: %s:%s, skipping.' % (cfg_file, section))
          continue

        if 'metric' not in parser[section] and\
           'relativePath' not in parser[section] and\
           'yTitle' not in parser[section]:
          print('Plot missing required attributes: %s:%s, skipping.' % (cfg_file, section))
          print('Required parameters: metric, relativePath, yTitle')
          continue
        trend_count+=1

        plot_title = parser[section]['yTitle']
        if 'plotTitle' in parser[section]:
          plot_title = parser[section]['plotTitle']

        if runs == None:
          runs_filter = ''
        else:
          runs_filter = 'AND run IN (%s)' % ', '.join(str(x) for x in runs)
        
        sql='''
        SELECT id, run, lumi, dataset, me_blob FROM monitor_elements
        WHERE me_path IN :me_path
        %s
        LIMIT 10
        ;
        ''' % runs_filter
        
        main_mes = []
        optional1_mes = []
        optional2_mes = []

        session = db_access.get_session()
        try:
          # ME paths in the config can be a comma separateed lists. 
          # This is to account for the DQM ME name changes.
          # Make sure to get all MEs if that's the case. 
          main_mes = session.execute(sql, {'me_path': tuple(parser[section]['relativePath'].split(',')) })
          if 'histo1Path' in parser[section]:
            optional1_mes = session.execute(sql, {'me_path': tuple(parser[section]['histo1Path'].split(',')) })
          if 'histo2Path' in parser[section]:
            optional2_mes = session.execute(sql, {'me_path': tuple(parser[section]['histo2Path'].split(',')) })
        except Exception as e:
          print(e)
        finally:
          session.close()

        for me in main_mes:
          optional1_me = None
          optional2_me = None

          tdirectories = []
          main_plot, main_tdir = get_plot_from_blob(me['me_blob'])
          tdirectories.append(main_tdir)

          metric = eval(parser[section]['metric'], {'fits': fits, 'basic': basic})

          if 'threshold' in parser[section]:
            metric.setThreshold(parser[section]['threshold'])

          if 'histo1Path' in parser[section]:
            optional1_me = next((x for x in optional1_mes if\
              x['run'] == me['run'] and x['lumi'] == me['lumi'] and x['dataset'] == me['dataset']), None)
            optional1_plot, optional1_tdir = get_plot_from_blob(optional1_me['me_blob'])
            tdirectories.append(optional1_tdir)
            metric.setOptionalHisto1(optional1_plot)

          if 'histo2Path' in parser[section]:
            optional2_me = next((x for x in optional2_mes if\
              x['run'] == me['run'] and x['lumi'] == me['lumi'] and x['dataset'] == me['dataset']), None)
            optional2_plot, optional2_tdir = get_plot_from_blob(optional2_me['me_blob'])
            tdirectories.append(optional2_tdir)
            metric.setOptionalHisto2(optional2_plot)

          # Calculate
          value, error = metric.calculate(main_plot)
          
          # Close all open TDirectories
          for tdirectory in tdirectories:
            tdirectory.Close()
          
          # Write results to the DB
          historic_data = db_access.HistoricData(
            run = me['run'],
            lumi = me['lumi'],
            subsystem = subsystem,
            name = section.split(':')[1],
            dataset = me['dataset'],
            pd = me['dataset'].split('/')[1],
            y_title = parser[section]['yTitle'],
            plot_title = plot_title,
            value = value,
            error = error,
            main_me_id = me['id']
          )

          if optional1_me:
            historic_data.optional_me1_id = optional1_me['id']
          if optional2_me:
            historic_data.optional_me2_id = optional2_me['id']

          session = db_access.get_session()
          try:
            session.add(historic_data)
            session.commit()
          except IntegrityError as e:
            print('Insert HistoricData error: %s' % e)
            session.rollback()
            print('Updating...')
            try:
              historic_data_existing = session.query(db_access.HistoricData).filter(
              db_access.HistoricData.run == historic_data.run,
              db_access.HistoricData.lumi == historic_data.lumi,
              db_access.HistoricData.subsystem == historic_data.subsystem,
              db_access.HistoricData.name == historic_data.name,
              ).one_or_none()

              if historic_data_existing:
                historic_data_existing.dataset = historic_data.dataset
                historic_data_existing.pd = historic_data.pd
                historic_data_existing.y_title = historic_data.y_title
                historic_data_existing.plot_title = historic_data.plot_title
                historic_data_existing.value = historic_data.value
                historic_data_existing.error = historic_data.error
                session.commit()
                print('Updated.')
            except Exception as e:
              print('Update HistoricData error: %s' % e)
              session.rollback()
          finally:
            session.close()
    except Exception as e:
      print(e)
      print('Could not read %s, skipping.' % cfg_file)

  print('Done processing %s trends.' % trend_count)


# Returns a ROOT plot from binary file
def get_plot_from_blob(me_blob):
  with tempfile.NamedTemporaryFile() as temp_file:
    with open(temp_file.name, 'w+b') as fd:
      fd.write(me_blob)
    tdirectory = ROOT.TFile(temp_file.name, 'read')
    plot = tdirectory.GetListOfKeys()[0].ReadObj()
    return plot, tdirectory


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
