from flask import Flask, jsonify, request, redirect
import os, sys
import json
import timeit
import requests
import psycopg2
# Insert parent dir to sys.path to import db_access and cern_sso
sys.path.insert(1, os.path.realpath(os.path.pardir))
import db_access
import decorators
from cern_sso import get_cookies

from sqlalchemy import text
from functools import partial
from multiprocessing import Pool
from collections import defaultdict

ALLOWED_PROCESSING_STRINGS = ['PromptReco', '09Aug2019_UL2017', 'Express', 'ExpressCosmics']

app = Flask(__name__)

@app.route('/api/data', methods=['GET'])
def data():
  subsystem = request.args.get('subsystem')
  pd = request.args.get('pd')
  processing_string = request.args.get('processing_string')
  from_run = request.args.get('from_run', type=int)
  to_run = request.args.get('to_run', type=int)
  runs = request.args.get('runs')
  latest = request.args.get('latest', type=int)
  series = request.args.get('series')
  series_id = request.args.get('series_id', type=int)

  if series_id == None:
    if subsystem == None:
      return jsonify({'message': 'Please provide a subsystem parameter.'}), 400

    if pd == None:
      return jsonify({'message': 'Please provide a pd parameter.'}), 400

    if processing_string == None:
      return jsonify({'message': 'Please provide a processing_string parameter.'}), 400

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

  if series and series_id:
    return jsonify({'message': 'series and series_id can not be defined at the same time.'}), 400

  db_access.setup_db()
  session = db_access.get_session()

  # Get series data by series_id
  if series_id:
    sql = '''
    SELECT selection_params.subsystem, selection_params.pd, selection_params.processing_string, last_calculated_configs.name
    FROM selection_params
    JOIN last_calculated_configs ON config_id = last_calculated_configs.id
    WHERE selection_params.id = :id
    ;
    '''

    rows = execute_with_retry(session, sql, { 'id': series_id })
    rows = list(rows)

    subsystem = rows[0]['subsystem']
    pd = rows[0]['pd']
    processing_string = rows[0]['processing_string']
    series = rows[0]['name']
  
  if (from_run == None or to_run == None) and runs == None:
    if latest == None:
      latest = 50

    run_class_like = '%%collision%%'
    if 'cosmic' in pd.lower():
      run_class_like = '%%cosmic%%'
    
    # Get latest runs for specific user selection
    sql = '''
    SELECT run FROM oms_data_cache
    WHERE run IN 
    (
      SELECT run FROM historic_data_points
      WHERE subsystem=:subsystem
      AND pd=:pd
      AND processing_string=:processing_string
    )
    AND oms_data_cache.run_class %s :run_class
    AND oms_data_cache.significant=%s
    AND oms_data_cache.is_dcs=%s
    ORDER BY run DESC
    LIMIT :latest
    ;
    ''' % (db_access.ilike_crossdb(), db_access.true_crossdb(), db_access.true_crossdb())

    print('Getting the list of runs...')
    start = timeit.default_timer() 

    rows = execute_with_retry(session, sql, { 'subsystem': subsystem, 'pd': pd, 'processing_string': processing_string, 'run_class': run_class_like, 'latest': latest })
    rows = list(rows)

    stop = timeit.default_timer()
    print('Runs retrieved in: ', stop - start)

    runs = [x[0] for x in rows]

  # Construct SQL query
  query_params  = { 'subsystem': subsystem, 'pd': pd, 'processing_string': processing_string }

  run_selection_sql = 'AND historic_data_points.run BETWEEN :from_run AND :to_run'
  if runs != None:
    run_selection_sql = 'AND historic_data_points.run IN (%s)' % ', '.join(str(x) for x in runs)
    query_params['runs'] = runs
  else:
    query_params['from_run'] = from_run
    query_params['to_run'] = to_run

  series_filter_sql = ''
  if series != None:
    series_filter_sql = 'AND historic_data_points.name IN ('
    series = series.split(',')
    for i in range(len(series)):
      key = 'series_%i' % i
      series_filter_sql += ':%s,' % key
      query_params[key] = series[i]
    series_filter_sql = series_filter_sql.rstrip(',') + ')'

  sql = '''
  SELECT 
  historic_data_points.id,
	historic_data_points.run, 
	historic_data_points.lumi, 
	historic_data_points.value, 
	historic_data_points.error,
	historic_data_points.name, 
	
	historic_data_points.dataset, 
	historic_data_points.pd, 
	historic_data_points.subsystem,
	
	historic_data_points.plot_title, 
	historic_data_points.y_title
  FROM historic_data_points

  WHERE historic_data_points.subsystem=:subsystem
  AND historic_data_points.pd=:pd
  AND historic_data_points.processing_string=:processing_string

  %s
  %s

  ORDER BY historic_data_points.run ASC
  ;
  ''' % (run_selection_sql, series_filter_sql)

  print('Getting the data...')
  start = timeit.default_timer() 

  rows = execute_with_retry(session, sql, query_params)
  rows = list(rows)
  session.close()

  stop = timeit.default_timer()
  print('Data retrieved in: ', stop - start)

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
        },
        'trends': []
      }

    result[key]['trends'].append({
      'run': row['run'],
      'lumi': row['lumi'],
      'value': row['value'],
      'error': row['error'],
      'id': row['id'],
      'oms_info': {},
    })

  # Transform result to array
  result = [result[key] for key in sorted(result.keys())]
  result = add_oms_info_to_result(result)

  return jsonify(result)


@app.route('/api/selection', methods=['GET'])
def selection():
  db_access.setup_db()

  session = db_access.get_session()
  try:
    obj = defaultdict(lambda: defaultdict(list))
    rows = execute_with_retry(session, 'SELECT DISTINCT subsystem, pd, processing_string FROM selection_params ORDER BY subsystem, pd, processing_string;')
    rows = list(rows)
    for row in rows:
      if(row['processing_string'] in ALLOWED_PROCESSING_STRINGS):
        obj[row['subsystem']][row['pd']].append(row['processing_string'])

    return jsonify(obj)
  finally:
    session.close()


@app.route('/api/plot_selection', methods=['GET'])
def plot_selection():
  db_access.setup_db()

  session = db_access.get_session()
  try:
    obj = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))

    rows = execute_with_retry(session, '''
    SELECT selection_params.id, selection_params.subsystem, selection_params.pd, selection_params.processing_string, last_calculated_configs.name 
    FROM selection_params 
    JOIN last_calculated_configs ON config_id = last_calculated_configs.id 
    ORDER BY selection_params.subsystem, selection_params.pd, selection_params.processing_string, last_calculated_configs.name
    ;
    ''')
    rows = list(rows)

    for row in rows:
      if(row['processing_string'] in ALLOWED_PROCESSING_STRINGS):
        obj[row['subsystem']][row['pd']][row['processing_string']].append({'name': row['name'], 'id': row['id']})

    return jsonify(obj)
  finally:
    session.close()


@app.route('/api/runs', methods=['GET'])
def runs():
  db_access.setup_db()
  session = db_access.get_session()

  runs = [h.run for h in session.query(db_access.HistoricDataPoint.run).distinct().order_by(db_access.HistoricDataPoint.run.asc())]
  session.close()
  return jsonify(runs)


@app.route('/api/expand_url', methods=['GET'])
def expand_url():
  valid_url_types = [
    'main_gui_url', 'main_image_url', 
    'optional1_gui_url', 'optional1_image_url', 
    'optional2_gui_url', 'optional2_image_url', 
    'reference_gui_url', 'reference_image_url'
  ]

  data_point_id = request.args.get('data_point_id', type=int)
  url_type = request.args.get('url_type')

  if data_point_id == None:
    return jsonify({'message': 'Please provide a data_point_id parameter.'}), 400

  if url_type not in valid_url_types:
    return jsonify({
      'message': 'Please provide a valid url_type parameter. Accepted values are: %s' % ','.join(valid_url_types)
    }), 400

  db_access.setup_db()
  session = db_access.get_session()

  try:
    sql = '''
    SELECT %s 
    FROM historic_data_points 
    WHERE id = :id
    ;
    ''' % url_type

    rows = list(execute_with_retry(session, sql, {'id': data_point_id}))
    url = rows[0][url_type]
    url = url.replace('+', '%2B')

    if url:
      return redirect(url, code=302)
    else:
      return jsonify({'message': 'Requested URL type is not found.'}), 404
  except Exception as e:
    print(e)
  finally:
    session.close()

  return jsonify({'message': 'Error getting the url from the DB.'}), 500


@app.route('/api/')
def index():
  return jsonify('HDQM REST API')


def add_oms_info_to_result(result):
  runs = set()
  for item in result:
    for trend in item['trends']:
      runs.add(trend['run'])
  runs = list(runs)

  db_access.dispose_engine()
  session = db_access.get_session()
    
  query = session.query(db_access.OMSDataCache)\
    .filter(db_access.OMSDataCache.run.in_(tuple(runs)))\
    .all()
  db_oms_data = list(query)
  session.close()

  oms_data_dict = defaultdict(list)
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

  # Add oms_info to the respose
  for item in result:
    for trend in item['trends']:
      trend['oms_info'] = oms_data_dict[trend['run']]

  return result


def execute_with_retry(session, sql, params=None):
  try:
    result = session.execute(sql, params)
  except psycopg2.OperationalError as e:
    print('Retrying:')
    print(e)
    session = db_access.get_session()
    result = session.execute(sql)
  return result


@app.after_request
def add_ua_compat(response):
  response.headers['Access-Control-Allow-Origin'] = '*'
  return response


if __name__ == '__main__':
  port=5000
  if len(sys.argv) >= 2:
    port=int(sys.argv[1])
  app.run(host='127.0.0.1', port=port)
