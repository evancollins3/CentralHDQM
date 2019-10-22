from flask import Flask, jsonify, request

import os, sys
# Insert parent dir to sys.path to import db_access
sys.path.insert(1, os.path.realpath(os.path.pardir))
import db_access

app = Flask(__name__)

@app.route('/historic_data', methods=['GET'])
def historic_data():
  from_run = request.args.get('from_run', type=int)
  to_run = request.args.get('to_run', type=int)

  if from_run == None or to_run == None:
    return jsonify({'message': 'Please provide from_run and to_run url parameters.'}), 400

  obj = {'from': from_run, 'to': to_run}
  return jsonify(obj)

@app.route('/metadata')
def metadata():
  db_access.setup_db()
  session = db_access.get_session()

  session.query(db_access.HistoricData.subsystem).distinct()

  obj = {'aa': 2, 'bb': 'asadasdasdasd'}
  return jsonify(obj)

@app.route('/')
def index():
  return jsonify('HDQM REST API')

if __name__ == '__main__':
  app.run(host='127.0.0.1', port=5000)
