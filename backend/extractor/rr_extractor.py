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
PREMADE_COOKIE='../api/etc/rr_sso_cookie.txt'

def fetch(update):
  db_access.setup_db()

  min_run = 0
  max_run = 0

  session = db_access.get_session()
  try:
    print('Getting min and max runs...')
    minmax = list(session.execute('SELECT MIN(run), MAX(run) FROM oms_data_cache;'))
    min_run = minmax[0][0]
    max_run = minmax[0][1]
  finally:
    session.close()

  print('Run range: %s-%s' % (min_run, max_run))

  fetch_runs(min_run, max_run)


def fetch_runs(min_run, max_run):
  url = 'https://cmsrunregistry.web.cern.ch/api/json_creation/generate'

  request = '''
  {
    "and": [
      {
        "or": [
          {"==": [{"var": "dataset.name"}, "online"]}
        ]
      },
      {">=": [{"var":"run.run_number"}, %s]},
      {"<=": [{"var":"run.run_number"}, %s]},
      {"==": [{"in": ["WMass", {"var": "run.oms.hlt_key"}]}, false]},
      {"==": [{"var": "lumisection.oms.cms_active"}, true]},
      {"==": [{"var": "lumisection.oms.bpix_ready"}, true]},
      {"==": [{"var": "lumisection.oms.fpix_ready"}, true]},
      {"==": [{"var": "lumisection.oms.tibtid_ready"}, true]},
      {"==": [{"var": "lumisection.oms.tecm_ready"}, true]},
      {"==": [{"var": "lumisection.oms.tecp_ready"}, true]},
      {"==": [{"var": "lumisection.oms.tob_ready"}, true]},
      {"==": [{"var": "lumisection.oms.ebm_ready"}, true]},
      {"==": [{"var": "lumisection.oms.ebp_ready"}, true]},
      {"==": [{"var": "lumisection.oms.eem_ready"}, true]},
      {"==": [{"var": "lumisection.oms.eep_ready"}, true]},
      {"==": [{"var": "lumisection.oms.esm_ready"}, true]},
      {"==": [{"var": "lumisection.oms.esp_ready"}, true]},
      {"==": [{"var": "lumisection.oms.hbhea_ready"}, true]},
      {"==": [{"var": "lumisection.oms.hbheb_ready"}, true]},
      {"==": [{"var": "lumisection.oms.hbhec_ready"}, true]},
      {"==": [{"var": "lumisection.oms.hf_ready"}, true]},
      {"==": [{"var": "lumisection.oms.ho_ready"}, true]},
      {"==": [{"var": "lumisection.oms.dtm_ready"}, true]},
      {"==": [{"var": "lumisection.oms.dtp_ready"}, true]},
      {"==": [{"var": "lumisection.oms.dt0_ready"}, true]},
      {"==": [{"var": "lumisection.oms.cscm_ready"}, true]},
      {"==": [{"var": "lumisection.oms.cscp_ready"}, true]},
      {"==": [{"var": "lumisection.oms.rpc_ready"}, true]}
    ]
  }
  ''' % (min_run, max_run)
    
  try:
    cookies = get_sso_cookie(url)
    result_json = json.loads(requests.post(url, json={ 'json_logic': request }, cookies=cookies, verify=CACERT).text)
    runs = result_json['final_json']

    sql = 'UPDATE oms_data_cache SET in_dcs_only=%s WHERE run = :run_nr RETURNING id;' % db_access.true_crossdb()
    for run in runs:
      session = db_access.get_session()
      try:
        result = session.execute(sql, {'run_nr': run})
        result = list(result)
        if len(result) == 0:
          print('Run not present in OMS cache: %s' % run)
        session.commit()
      except Exception as e:
        print(e)
        session.rollback()
      finally:
        session.close()
  except Exception as e:
    print(e)


def get_sso_cookie(url):
  if os.path.isfile(CERT) and os.path.isfile(KEY) and os.path.isfile(CACERT):
    return get_cookies(url, usercert=CERT, userkey=KEY, verify=CACERT)
  elif os.path.isfile(PREMADE_COOKIE):
    cookies = {}
    with open(PREMADE_COOKIE, 'r') as file:
      for line in file:
        fields = line.strip().split('\t')
        if len(fields) == 7:
          cookies[fields[5]] = fields[6]
    return cookies
  return None


if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='DCS data extraction from the RR API.')
  parser.add_argument('-u', dest='update', type=bool, default=False, help='If True, all runs will be updated. Otherwise only missing runs will be fetched.')
  args = parser.parse_args()

  update = args.update
  fetch(update)
