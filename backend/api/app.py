from flask import Flask, jsonify, request

import os, sys
import json
import requests
# Insert parent dir to sys.path to import db_access
sys.path.insert(1, os.path.realpath(os.path.pardir))
import db_access
from multiprocessing import Pool
from cern_sso import get_cookies
from sqlalchemy import text
from functools import partial

PROCESSING_LEVELS = ['PromptReco', 'UltraLegacy']
CERT='private/usercert.pem'
KEY='private/userkey.pem'
CACERT='etc/cern_cacert.pem'

app = Flask(__name__)

@app.route('/data', methods=['GET'])
def data():
  # raise Exception
  subsystem = request.args.get('subsystem')
  processing_level = request.args.get('processing_level', default=PROCESSING_LEVELS[0])
  from_run = request.args.get('from_run', type=int)
  to_run = request.args.get('to_run', type=int)
  runs = request.args.get('runs')
  latest = request.args.get('latest', type=int)
  series = request.args.get('series')

  if subsystem == None:
    return jsonify({'message': 'Please provide a subsystem parameter.'}), 400

  if processing_level not in PROCESSING_LEVELS:
    return jsonify({'message': 'Please provide a valid processing_level parameter. Allowed values: %s' % ', '.join(PROCESSING_LEVELS)}), 400

  modes = 0
  if from_run != None and to_run != None: modes += 1
  if latest != None: modes += 1
  if runs != None: modes += 1

  if modes > 1:
    return jsonify({'message': 'The combination of parameters you provided is invalid.'}), 400

  if runs != None:
    try:
      runs = runs.split(',')
      runs = [int(x) for x in runs]
    except:
      return jsonify({'message': 'runs parameter is not valid. It has to be a comma separated list of integers.'}), 400

  db_access.setup_db()
  session = db_access.get_session()
  
  if (from_run == None or to_run == None) and runs == None:
    if latest == None:
      latest = 50
    
    query = session.query(db_access.HistoricData.run)\
      .distinct()\
      .order_by(db_access.HistoricData.run.desc())\
      .limit(latest)
    latest_runs = list(query)
    if len(latest_runs) > 0:
      from_run = latest_runs[-1][0]
      to_run = latest_runs[0][0]
    else:
      from_run = to_run = 0

  # Construct SQL query
  query_params  = {'subsystem': subsystem, 'processing_level': '%' + processing_level + '%'}

  run_selection_sql = 'AND run BETWEEN :from_run AND :to_run'
  if runs != None:
    run_selection_sql = 'AND run IN (%s)' % ', '.join(str(x) for x in runs)
    query_params['runs'] = runs
  else:
    query_params['from_run'] = from_run
    query_params['to_run'] = to_run

  series_filter_sql = ''
  if series != None:
    series_filter_sql = 'AND name IN ('
    series = series.split(',')
    for i in range(len(series)):
      key = 'series_%i' % i
      series_filter_sql += ':%s,' % key
      query_params[key] = series[i]
    series_filter_sql = series_filter_sql.rstrip(',') + ')'

  sql = '''
  -- Group by (run, lumi, subsystem, name) and MAX the dataset name.
  -- Thiw will filter out each group and give us correct datasets to be used
  -- but not the values. Join it with the original table to get the remianing values.
  SELECT original.*, mes.gui_url, mes.image_url, mes.me_path
  FROM
    (SELECT run,
            lumi,
            subsystem,
            name,
            MAX(dataset) AS max_dataset
    FROM historic_data

    WHERE subsystem = :subsystem
    AND lumi = '0'
    AND LOWER(dataset) LIKE LOWER(:processing_level)
    %s
    %s

    GROUP BY run,
              lumi,
              subsystem,
              name) AS grouped
  JOIN historic_data original ON original.run = grouped.run
    AND original.lumi = grouped.lumi
    AND original.subsystem = grouped.subsystem
    AND original.name = grouped.name
    AND original.dataset = grouped.max_dataset 

  -- Get the me info
  JOIN monitor_elements AS mes ON original.main_me_id = mes.id

  ORDER BY original.run ASC
  ;
  ''' % (run_selection_sql, series_filter_sql)
  
  rows = session.execute(sql, query_params)
  rows = list(rows)
  session.close()

  result = {}
  for row in rows:
    # Names are unique within the subsystem
    key = '%s_%s' % (row['name'], row['subsystem'])
    if key not in result:
      result[key] = {
        'metadata': { 
          'y_title': row['y_title'], 
          'plot_title': row['plot_title'], 
          'name': row['name'], 
          'subsystem': row['subsystem'], 
          'me_path': row['me_path'],
        },
        'trends': []
      }

    result[key]['trends'].append({
      'run': row['run'],
      'lumi': row['lumi'],
      'value': row['value'],
      'error': row['error'],
      'gui_url': row['gui_url'],
      'image_url': row['image_url'],
      'oms_info': {},
    })

  # Transform result to array
  result = [result[key] for key in result.keys()]

  result = add_oms_info_to_result(result)

  return jsonify(result)


@app.route('/subsystems', methods=['GET'])
def subsystems():
  # raise Exception
  db_access.setup_db()
  session = db_access.get_session()

  subsystems = [{'subsystem': h.subsystem, 'processing_levels': PROCESSING_LEVELS} 
    for h in session.query(db_access.HistoricData.subsystem).distinct()]
  session.close()
  return jsonify(subsystems)


@app.route('/runs', methods=['GET'])
def runs():
  db_access.setup_db()
  session = db_access.get_session()

  runs = [h.run for h in session.query(db_access.HistoricData.run).distinct().order_by(db_access.HistoricData.run.asc())]
  session.close()
  return jsonify(runs)


@app.route('/')
def index():
  return jsonify('HDQM REST API')


def add_oms_info_to_result(result):
  runs = set()
  for item in result:
    for trend in item['trends']:
      runs.add(trend['run'])
  runs = list(runs)

  session = db_access.get_session()
    
  query = session.query(db_access.OMSDataCache)\
    .filter(db_access.OMSDataCache.run.in_(tuple(runs)))\
    .all()
  db_oms_data = list(query)
  session.close()

  oms_data_dict = {}
  for row in db_oms_data:
    oms_data_dict[row.run] = {
      'start_time': row.start_time,
      'end_time': row.end_time,
      'b_field': row.b_field,
      'energy': row.energy,
      'delivered_lumi': row.delivered_lumi,
      'end_lumi': row.end_lumi,
      'recorded_lumi': row.recorded_lumi,
      'l1_key': row.l1_key,
      'l1_rate': row.l1_rate,
      'hlt_key': row.hlt_key,
      'hlt_physics_rate': row.hlt_physics_rate,
      'duration': row.duration,
      'fill_number': row.fill_number,
      'injection_scheme': row.injection_scheme,
      'era': row.era,
    }

  # Keep runs that need to be fetched from OMS API
  runs = [run for run in runs if run not in oms_data_dict.keys()]

  # Fetch in a multithreaded manner
  pool = Pool(max(len(runs), 1))
  api_oms_data = pool.map(get_oms_info_from_api, runs)

  for row in api_oms_data:
    oms_data_dict.update(row)
    # key = list(row.keys())[0]

    # Add to cache
    # try:
    #   session = db_access.get_session()
    #   session.add(db_access.OMSDataCache(
    #     run = key,
    #     lumi = 0,
    #     start_time = row[key]['start_time'],
    #     end_time = row[key]['end_time'],
    #     b_field = row[key]['b_field'],
    #     energy = row[key]['energy'],
    #     delivered_lumi = row[key]['delivered_lumi'],
    #     end_lumi = row[key]['end_lumi'],
    #     recorded_lumi = row[key]['recorded_lumi'],
    #     l1_key = row[key]['l1_key'],
    #     l1_rate = row[key]['l1_rate'],
    #     hlt_key = row[key]['hlt_key'],
    #     hlt_physics_rate = row[key]['hlt_physics_rate'],
    #     duration = row[key]['duration'],
    #     fill_number = row[key]['fill_number'],
    #     injection_scheme = row[key]['injection_scheme'],
    #     era = row[key]['era'],
    #   ))
    #   session.commit()
    # except Exception as e:
    #   print(e)
    #   session.rollback()
    # finally:
    #   session.close()

  # Add oms_info to the respose
  for item in result:
    for trend in item['trends']:
      trend['oms_info'] = oms_data_dict[trend['run']]

  return result


def get_oms_info_from_api(run):
  runs_url = 'https://cmsoms.cern.ch/agg/api/v1/runs?filter[run_number][eq]=%s&fields=start_time,end_time,b_field,energy,delivered_lumi,end_lumi,recorded_lumi,l1_key,hlt_key,l1_rate,hlt_physics_rate,duration,fill_number' % run
  
  try:
    cookies = get_cookies(runs_url, usercert=CERT, userkey=KEY, verify=CACERT)
    oms_runs_json = json.loads(requests.get(runs_url, cookies=cookies, verify=CACERT).text)

    fills_url = 'https://cmsoms.cern.ch/agg/api/v1/fills?filter[fill_number][eq]=%s&fields=injection_scheme,era' % oms_runs_json['data'][0]['attributes']['fill_number']
    oms_fills_json = json.loads(requests.get(fills_url, cookies=cookies, verify=CACERT).text)

    result = {
      'start_time': oms_runs_json['data'][0]['attributes']['start_time'],
      'end_time': oms_runs_json['data'][0]['attributes']['end_time'],
      'b_field': oms_runs_json['data'][0]['attributes']['b_field'],
      'energy': oms_runs_json['data'][0]['attributes']['energy'],
      'delivered_lumi': oms_runs_json['data'][0]['attributes']['delivered_lumi'],
      'end_lumi': oms_runs_json['data'][0]['attributes']['end_lumi'],
      'recorded_lumi': oms_runs_json['data'][0]['attributes']['recorded_lumi'],
      'l1_key': oms_runs_json['data'][0]['attributes']['l1_key'],
      'l1_rate': oms_runs_json['data'][0]['attributes']['l1_rate'],
      'hlt_key': oms_runs_json['data'][0]['attributes']['hlt_key'],
      'hlt_physics_rate': oms_runs_json['data'][0]['attributes']['hlt_physics_rate'],
      'duration': oms_runs_json['data'][0]['attributes']['duration'],
      'fill_number': oms_runs_json['data'][0]['attributes']['fill_number'],
      'injection_scheme': oms_fills_json['data'][0]['attributes']['injection_scheme'],
      'era': oms_fills_json['data'][0]['attributes']['era'],
    }

    # Add to cache
    try:
      session = db_access.get_session()
      session.add(db_access.OMSDataCache(
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
      ))
      session.commit()
    except Exception as e:
      print(e)
      session.rollback()
    finally:
      session.close()

    return { run: result }
  except Exception as e:
    print(e)


if __name__ == '__main__':
  app.run(host='127.0.0.1', port=5000)
