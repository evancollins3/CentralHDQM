from flask import Flask, jsonify, request
import os, sys
import json
import requests
# Insert parent dir to sys.path to import db_access and cern_sso
sys.path.insert(1, os.path.realpath(os.path.pardir))
import db_access
from cern_sso import get_cookies

from sqlalchemy import text
from functools import partial
from multiprocessing import Pool
from collections import defaultdict

CERT='private/usercert.pem'
KEY='private/userkey.pem'
CACERT='etc/cern_cacert.pem'
PREMADE_COOKIE='etc/sso_cookie.txt'

app = Flask(__name__)

@app.route('/data', methods=['GET'])
def data():
  # raise Exception
  subsystem = request.args.get('subsystem')
  pd = request.args.get('pd')
  processing_string = request.args.get('processing_string')
  from_run = request.args.get('from_run', type=int)
  to_run = request.args.get('to_run', type=int)
  runs = request.args.get('runs')
  latest = request.args.get('latest', type=int)
  series = request.args.get('series')

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

  db_access.setup_db()
  session = db_access.get_session()
  
  if (from_run == None or to_run == None) and runs == None:
    if latest == None:
      latest = 50
    
    # Get latest runs for specific user selection
    sql = '''
    SELECT DISTINCT(run) FROM historic_data_points
    WHERE subsystem=:subsystem
    AND pd=:pd
    AND processing_string=:processing_string
    ORDER BY run DESC
    LIMIT %s
    ;
    ''' % latest

    rows = session.execute(sql, { 'subsystem': subsystem, 'pd': pd, 'processing_string': processing_string })
    rows = list(rows)

    from_run = to_run = 0
    if len(rows) >= 2:
      from_run = rows[-1][0]
      to_run = rows[0][0]
    elif len(rows) == 1:
      from_run = to_run = rows[0][0]

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
    series_filter_sql = 'AND last_calculated_configs.name IN ('
    series = series.split(',')
    for i in range(len(series)):
      key = 'series_%i' % i
      series_filter_sql += ':%s,' % key
      query_params[key] = series[i]
    series_filter_sql = series_filter_sql.rstrip(',') + ')'

  sql = '''
  SELECT 
	historic_data_points.run, 
	historic_data_points.lumi, 
	historic_data_points.value, 
	historic_data_points.error, 
	historic_data_points.subsystem, 
	last_calculated_configs.name, 
	last_calculated_configs.plot_title, 
	last_calculated_configs.y_title, 
	last_calculated_configs.relative_path AS main_me_path,
	last_calculated_configs.histo1_path AS optional1_me_path, 
	last_calculated_configs.histo2_path AS optional2_me_path, 
	last_calculated_configs.reference_path, 
	mes.gui_url AS main_gui_url,
	mes.image_url AS main_image_url,
	optional_mes_1.gui_url AS optional1_gui_url,
	optional_mes_1.image_url AS optional1_image_url,
	optional_mes_2.gui_url AS optional2_gui_url,
	optional_mes_2.image_url AS optional2_image_url,
	reference_mes.gui_url AS reference_gui_url,
	reference_mes.image_url AS reference_image_url
  FROM historic_data_points

  -- Join the shared config values
  JOIN last_calculated_configs ON historic_data_points.config_id = last_calculated_configs.id

  -- join ME data
  JOIN monitor_elements AS mes ON historic_data_points.main_me_id = mes.id
  LEFT OUTER JOIN monitor_elements AS optional_mes_1 ON historic_data_points.optional_me1_id = optional_mes_1.id
  LEFT OUTER JOIN monitor_elements AS optional_mes_2 ON historic_data_points.optional_me2_id = optional_mes_2.id
  LEFT OUTER JOIN monitor_elements AS reference_mes ON historic_data_points.reference_me_id = reference_mes.id

  WHERE historic_data_points.subsystem=:subsystem
  AND historic_data_points.pd=:pd
  AND historic_data_points.processing_string=:processing_string

  %s
  %s

  ORDER BY historic_data_points.run ASC
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
          'main_me_path': row['main_me_path'],
          'optional1_me_path': row['optional1_me_path'],
          'optional2_me_path': row['optional2_me_path'],
        },
        'trends': []
      }

    result[key]['trends'].append({
      'run': row['run'],
      'lumi': row['lumi'],
      'value': row['value'],
      'error': row['error'],
      'main_gui_url': row['main_gui_url'],
      'main_image_url': row['main_image_url'],
      'optional1_gui_url': row['optional1_gui_url'],
      'optional1_image_url': row['optional1_image_url'],
      'optional2_gui_url': row['optional2_gui_url'],
      'optional2_image_url': row['optional2_image_url'],
      'oms_info': {},
    })

  # Transform result to array
  result = [result[key] for key in sorted(result.keys())]

  # result = add_oms_info_to_result(result)

  return jsonify(result)


@app.route('/selection', methods=['GET'])
def selection():
  db_access.setup_db()

  session = db_access.get_session()
  try:
    obj = defaultdict(lambda: defaultdict(list))
    flat = list(session.execute('SELECT subsystem, pd, processing_string FROM selection_params ORDER BY subsystem, pd, processing_string;'))
    for row in flat:
      obj[row['subsystem']][row['pd']].append(row['processing_string'])

    return jsonify(obj)
  finally:
    session.close()


@app.route('/runs', methods=['GET'])
def runs():
  db_access.setup_db()
  session = db_access.get_session()

  runs = [h.run for h in session.query(db_access.HistoricDataPoint.run).distinct().order_by(db_access.HistoricDataPoint.run.asc())]
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

  # Keep runs that need to be fetched from OMS API
  runs = [run for run in runs if run not in oms_data_dict]

  # Fetch in a multithreaded manner
  pool = Pool(20)
  api_oms_data = pool.map(get_oms_info_from_api, runs)

  for row in api_oms_data:
    if row:
      oms_data_dict.update(row)

  # Add oms_info to the respose
  for item in result:
    for trend in item['trends']:
      trend['oms_info'] = oms_data_dict[trend['run']]

  return result


def get_oms_info_from_api(run):
  db_access.dispose_engine()
  runs_url = 'https://cmsoms.cern.ch/agg/api/v1/runs?filter[run_number][eq]=%s&fields=start_time,end_time,b_field,energy,delivered_lumi,end_lumi,recorded_lumi,l1_key,hlt_key,l1_rate,hlt_physics_rate,duration,fill_number' % run
  
  try:
    # cookies = get_cookies(runs_url, usercert=CERT, userkey=KEY, verify=CACERT)
    cookies = get_sso_cookie(runs_url)
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


def get_sso_cookie(url):
  if os.path.isfile(CERT) and os.path.isfile(KEY) and os.path.isfile(CACERT):
    return get_cookies(url, usercert=CERT, userkey=KEY, verify=CACERT)
  elif os.path.isfile(PREMADE_COOKIE):
    with open(PREMADE_COOKIE, 'r') as file:
      return file.read()
  return None


@app.after_request
def add_ua_compat(response):
  response.headers['Access-Control-Allow-Origin'] = '*'
  return response


if __name__ == '__main__':
  port=5000
  if len(sys.argv) >= 2:
    port=int(sys.argv[1])
  app.run(host='127.0.0.1', port=port)
