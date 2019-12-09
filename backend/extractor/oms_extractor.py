#!/usr/bin/env python3
from __future__ import print_function

from sys import argv
from multiprocessing import Pool
from sqlalchemy.exc import IntegrityError

import json
import requests
import argparse

import os, sys
# Insert parent dir to sys.path to import db_access and cern_sso
sys.path.insert(1, os.path.realpath(os.path.pardir))
import db_access
from cern_sso import get_cookies

CERT='../api/private/usercert.pem'
KEY='../api/private/userkey.pem'
CACERT='../api/etc/cern_cacert.pem'


def fetch(update):
  db_access.setup_db()

  all_runs = []
  extracted_runs = []

  session = db_access.get_session()
  try:
    all_runs = list(session.execute('SELECT DISTINCT(run) FROM historic_data_points;'))
    all_runs = [x[0] for x in all_runs]
    extracted_runs = list(session.execute('SELECT DISTINCT(run) FROM oms_data_cache;'))
    extracted_runs = [x[0] for x in extracted_runs]
  finally:
    session.close()

  # Diff needs to be extracted!
  if update:
    diff = all_runs
  else:
    diff = [x for x in all_runs if x not in extracted_runs]

  for run in diff:
    db_access.dispose_engine()
    print('Extracting run: %s...' % run)
    runs_url = 'https://cmsoms.cern.ch/agg/api/v1/runs?filter[run_number][eq]=%s&fields=start_time,end_time,b_field,energy,delivered_lumi,end_lumi,recorded_lumi,l1_key,hlt_key,l1_rate,hlt_physics_rate,duration,fill_number' % run
    
    try:
      cookies = get_cookies(runs_url, usercert=CERT, userkey=KEY, verify=CACERT)
      oms_runs_json = json.loads(requests.get(runs_url, cookies=cookies, verify=CACERT).text)

      fills_url = 'https://cmsoms.cern.ch/agg/api/v1/fills?filter[fill_number][eq]=%s&fields=injection_scheme,era' % oms_runs_json['data'][0]['attributes']['fill_number']
      oms_fills_json = json.loads(requests.get(fills_url, cookies=cookies, verify=CACERT).text)

      # Add to cache
      try:
        session = db_access.get_session()
        oms_item = db_access.OMSDataCache(
          run = run,
          lumi = 0,
          start_time = oms_runs_json['data'][0]['attributes']['start_time'],
          end_time = oms_runs_json['data'][0]['attributes']['end_time'],
          b_field = oms_runs_json['data'][0]['attributes']['b_field'],
          energy = oms_runs_json['data'][0]['attributes']['energy'],
          delivered_lumi = oms_runs_json['data'][0]['attributes']['delivered_lumi'],
          end_lumi = oms_runs_json['data'][0]['attributes']['end_lumi'],
          recorded_lumi = oms_runs_json['data'][0]['attributes']['recorded_lumi'],
          l1_key = oms_runs_json['data'][0]['attributes']['l1_key'],
          l1_rate = oms_runs_json['data'][0]['attributes']['l1_rate'],
          hlt_key = oms_runs_json['data'][0]['attributes']['hlt_key'],
          hlt_physics_rate = oms_runs_json['data'][0]['attributes']['hlt_physics_rate'],
          duration = oms_runs_json['data'][0]['attributes']['duration'],
          fill_number = oms_runs_json['data'][0]['attributes']['fill_number'],
          injection_scheme = oms_fills_json['data'][0]['attributes']['injection_scheme'],
          era = oms_fills_json['data'][0]['attributes']['era'],
        )
        session.add(oms_item)
        session.commit()
      except IntegrityError as e:
        print('IntegrityError inserting OMS item: %s' % e)
        session.rollback()
        print('Updating...')
        try:
          oms_item_existing = session.query(db_access.OMSDataCache).filter(
            db_access.OMSDataCache.run == oms_item.run,
            db_access.OMSDataCache.lumi == oms_item.lumi
          ).one_or_none()

          if oms_item_existing:
            oms_item_existing.start_time = oms_item.start_time,
            oms_item_existing.end_time = oms_item.end_time,
            oms_item_existing.b_field = oms_item.b_field,
            oms_item_existing.energy = oms_item.energy,
            oms_item_existing.delivered_lumi = oms_item.delivered_lumi,
            oms_item_existing.end_lumi = oms_item.end_lumi,
            oms_item_existing.recorded_lumi = oms_item.recorded_lumi,
            oms_item_existing.l1_key = oms_item.l1_key,
            oms_item_existing.l1_rate = oms_item.l1_rate,
            oms_item_existing.hlt_key = oms_item.hlt_key,
            oms_item_existing.hlt_physics_rate = oms_item.hlt_physics_rate,
            oms_item_existing.duration = oms_item.duration,
            oms_item_existing.fill_number = oms_item.fill_number,
            oms_item_existing.injection_scheme = oms_item.injection_scheme,
            oms_item_existing.era = oms_item.era,
            session.commit()
            print('Updated.')
        except Exception as e:
          print(e)
          session.rollback()
      except Exception as e:
        print(e)
        session.rollback()
      finally:
        session.close()
    except Exception as e:
      print(e)


if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='HDQM data extraction from the OMS API.')
  parser.add_argument('-u', dest='update', type=bool, default=False, help='If True, all runs will be updated. Otherwise only missing runs will be fetched.')
  args = parser.parse_args()

  update = args.update
  fetch(update)
