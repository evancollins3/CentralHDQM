from __future__ import print_function
import os
import enum
from sqlalchemy import create_engine, text
from sqlalchemy import Column, String, Integer, Float, DateTime, Binary, Boolean, ForeignKey, Enum, UniqueConstraint, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

# SQLite will be used if no production DB credentials will be found
dir_path = os.path.dirname(os.path.realpath(__file__))
db_string = 'sqlite:///' + os.path.join(dir_path, 'hdqm.db')

prod_db_string_file = os.path.join(dir_path, 'connection_string.txt')
if os.path.isfile(prod_db_string_file):
  with open(prod_db_string_file, 'r') as file:
    db_string = file.readline()

is_postgres = True
if not db_string.startswith('postgres://'):
  is_postgres = False

db = create_engine(db_string)
base = declarative_base()


class HistoricDataPoint(base):
  __tablename__ = 'historic_data_points'

  id = Column(Integer, primary_key=True, nullable=False)
  run = Column(Integer, nullable=False)
  lumi = Column(Integer, nullable=False)
  dataset = Column(String, nullable=False)
  subsystem = Column(String, nullable=False)
  pd = Column(String, nullable=False)
  processing_string = Column(String, nullable=False)
  value = Column(Float, nullable=False)
  error = Column(Float, nullable=False)
  name = Column(String, nullable=False)
  plot_title = Column(String, nullable=False)
  y_title = Column(String, nullable=False)
  main_me_path = Column(String, nullable=False)
  main_gui_url = Column(String, nullable=False)
  main_image_url = Column(String, nullable=False)
  optional1_me_path = Column(String)
  optional1_gui_url = Column(String)
  optional1_image_url = Column(String)
  optional2_me_path = Column(String)
  optional2_gui_url = Column(String)
  optional2_image_url = Column(String)
  reference_path = Column(String)
  reference_gui_url = Column(String)
  reference_image_url = Column(String)

  # Foreign keys
  config_id = Column(Integer, ForeignKey('last_calculated_configs.id'), nullable=False)
  config = relationship("LastCalculatedConfig", foreign_keys=[config_id])
  main_me_id = Column(Integer, ForeignKey('monitor_elements.id'), nullable=False)
  main_me = relationship("MonitorElement", foreign_keys=[main_me_id])
  optional_me1_id = Column(Integer, ForeignKey('monitor_elements.id'))
  optional_me1 = relationship("MonitorElement", foreign_keys=[optional_me1_id])
  optional_me2_id = Column(Integer, ForeignKey('monitor_elements.id'))
  optional_me2 = relationship("MonitorElement", foreign_keys=[optional_me2_id])
  reference_me_id = Column(Integer, ForeignKey('monitor_elements.id'))
  reference_me = relationship("MonitorElement", foreign_keys=[reference_me_id])

  __table_args__ = (
    Index('_historic_data_points_config_id_main_me_id_uindex', 'config_id', 'main_me_id', unique=True),
    Index('_historic_data_points_run_subsystem_pd_processing_string_index', 'run', 'subsystem', 'pd', 'processing_string'),
    Index('_historic_data_points_covering_index', 'subsystem', 'pd', 'processing_string', 'run', 'lumi', 'value', 'error', 'name', 'dataset', 
      'plot_title', 'y_title', 'main_me_path', 'optional1_me_path', 'optional2_me_path', 'reference_path', 'main_gui_url', 'main_image_url', 
      'optional1_gui_url', 'optional1_image_url', 'optional2_gui_url', 'optional2_image_url', 'reference_gui_url', 'reference_image_url'
    ),
  )


class SelectionParams(base):
  __tablename__ = 'selection_params'

  id = Column(Integer, primary_key=True, nullable=False)
  subsystem = Column(String, nullable=False)
  pd = Column(String, nullable=False)
  processing_string = Column(String, nullable=False)

  # Foreign keys
  config_id = Column(Integer, ForeignKey('last_calculated_configs.id'), nullable=False)
  config = relationship("LastCalculatedConfig", foreign_keys=[config_id])

  __table_args__ = (
    Index('_selection_params_subsystem_pd_ps_config_id_uindex', 'subsystem', 'pd', 'processing_string', 'config_id', unique=True),
  )


class MonitorElement(base):
  __tablename__ = 'monitor_elements'

  id = Column(Integer, primary_key=True, nullable=False)
  run = Column(Integer, nullable=False)
  lumi = Column(Integer, nullable=False)
  me_path = Column(String, nullable=False)
  dataset = Column(String, nullable=False)
  eos_path = Column(String, nullable=False)
  gui_url = Column(String, nullable=False)
  image_url = Column(String, nullable=False)

  # Foreign keys
  me_blob_id = Column(Integer, ForeignKey('me_blobs.id'), nullable=False)
  me_blob = relationship("MeBlob", foreign_keys=[me_blob_id])

  __table_args__ = (
    Index('_monitor_element_me_path_index', 'me_path'),
    Index('_monitor_element_me_path_eos_path_uindex', 'me_path', 'eos_path', unique=True)
  )

class MeBlob(base):
  __tablename__ = 'me_blobs'

  id = Column(Integer, primary_key=True, nullable=False)
  me_blob = Column(Binary, nullable=False)


class OMSDataCache(base):
  __tablename__ = 'oms_data_cache'

  id = Column(Integer, primary_key=True, nullable=False)
  run = Column(Integer, nullable=False)
  lumi = Column(Integer, nullable=False)
  start_time = Column(DateTime, nullable=False)
  end_time = Column(DateTime, nullable=False)
  
  b_field = Column(Float, nullable=False)
  energy = Column(Float)
  
  delivered_lumi = Column(Float)
  end_lumi = Column(Float)
  recorded_lumi = Column(Float)
  l1_key = Column(String)
  hlt_key = Column(String, nullable=False)
  l1_rate = Column(Float)
  hlt_physics_rate = Column(Float)
  duration = Column(Integer, nullable=False)
  fill_number = Column(Integer, nullable=False)
  injection_scheme = Column(String)
  era = Column(String, nullable=False)

  in_dcs_only = Column(Boolean, nullable=False, default=False)

  __table_args__ = (
    Index('_oms_data_cache_run_lumi_uindex', 'run', 'lumi', unique=True),
  )


# ============== Tables for tracking the progress of monitor element extraction ============== #

class TrackedMEPathForMEExtraction(base):
  __tablename__ = 'tracked_me_paths_for_me_extraction'

  me_path = Column(String, primary_key=True, nullable=False)

  __table_args__ = (Index('_tracked_me_paths_for_me_extraction_me_path_uindex', 'me_path', unique=True),)


class TrackedEOSPathForMEExtraction(base):
  __tablename__ = 'tracked_eos_paths_for_me_extraction'

  eos_path = Column(String, primary_key=True, nullable=False)

  __table_args__ = (Index('_tracked_eos_paths_for_me_extraction_eos_path_uindex', 'eos_path', unique=True),)


class NewMEPathForMEExtraction(base):
  __tablename__ = 'new_me_paths_for_me_extraction'

  me_path = Column(String, primary_key=True, nullable=False)

  __table_args__ = (Index('_new_me_paths_for_me_extraction_me_path_uindex', 'me_path', unique=True),)


class NewEOSPathForMEExtraction(base):
  __tablename__ = 'new_eos_paths_for_me_extraction'

  eos_path = Column(String, primary_key=True, nullable=False)

  __table_args__ = (Index('_new_eos_paths_for_me_extraction_eos_path_uindex', 'eos_path', unique=True),)


class QueueToExtract(base):
  __tablename__ = 'queue_to_extract'

  id = Column(Integer, primary_key=True, nullable=False)
  eos_path = Column(String, nullable=False)
  me_path = Column(String, nullable=False)


# ================= Tables for tracking the progress of the trend calculation ================ #

class QueueToCalculate(base):
  __tablename__ = 'queue_to_calculate'

  id = Column(Integer, primary_key=True, nullable=False)

  # Foreign keys
  me_id = Column(Integer, ForeignKey('monitor_elements.id'), nullable=False)
  me = relationship("MonitorElement", foreign_keys=[me_id])


class QueueToCalculateLater(base):
  __tablename__ = 'queue_to_calculate_later'

  id = Column(Integer, primary_key=True, nullable=False)

  # Foreign keys
  me_id = Column(Integer, ForeignKey('monitor_elements.id'), nullable=False)
  me = relationship("MonitorElement", foreign_keys=[me_id])


class LastCalculatedConfig(base):
  __tablename__ = 'last_calculated_configs'

  id = Column(Integer, primary_key=True, nullable=False)
  subsystem = Column(String, nullable=False)
  name = Column(String, nullable=False)
  metric = Column(String, nullable=False)
  plot_title = Column(String, nullable=False)
  y_title = Column(String, nullable=False)
  relative_path = Column(String, nullable=False)
  histo1_path = Column(String)
  histo2_path = Column(String)
  reference_path = Column(String)
  threshold = Column(Integer)


# ====================================== Helper functions ==================================== #

def setup_db():
  try:
    base.metadata.create_all(db)
  except Exception as e:
    base.metadata.create_all(db)


def get_session():
  try:
    Session = sessionmaker(db)
    session = Session()
    return session
  except Exception as e:
    print('Exception creating session:', e)
    return None


def dispose_engine():
  db.dispose()


def vacuum_processed_mes():
  if is_postgres:
    connection = db.connect()
    connection = connection.execution_options(isolation_level='AUTOCOMMIT')
    try:
      connection.execute('VACUUM processed_monitor_elements;')
    except Exception as e:
      print(e)
    finally:
      connection.close()

# Transforms INSERT into a insert or ignore based on current Database backend. 
# SQLite and Postgres are supported
# Query has to begin with INSERT and end with a ;
def insert_or_ignore_crossdb(query):
  if is_postgres:
    return query.rstrip(';') + ' ON CONFLICT DO NOTHING;'
  else:
    return 'INSERT OR IGNORE' + query.lstrip('INSERT')


def true_crossdb():
  if is_postgres:
    return 'TRUE'
  else:
    return '1'


def false_crossdb():
  if is_postgres:
    return 'FALSE'
  else:
    return '0'


# Transforms an INSERT or UPDATE to return an ID of inserted or updated row(s)
def returning_id_crossdb(query):
  if is_postgres:
    return query.rstrip(';') + ' RETURNING id;'
  else:
    return query + ' last_insert_rowid();'


if __name__ == '__main__':
  setup_db()
