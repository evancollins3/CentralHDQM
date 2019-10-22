from __future__ import print_function
import enum
from sqlalchemy import create_engine
from sqlalchemy import Column, String, Integer, Float, DateTime, Binary, ForeignKey, Enum, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

with open('connection_string.txt', 'r') as file:
  db_string = file.read().replace('\n', '')
db = create_engine(db_string)
base = declarative_base()

class HistoricData(base):
  __tablename__ = 'historic_data'

  id = Column(Integer, primary_key=True, nullable=False)
  run = Column(Integer, nullable=False)
  lumi = Column(Integer, nullable=False)
  subsystem = Column(String, nullable=False)
  name = Column(String, nullable=False)
  dataset = Column(String, nullable=False)
  pd = Column(String, nullable=False)
  y_title = Column(String, nullable=False)
  value = Column(Float, nullable=False)
  error = Column(Float, nullable=False)

  # Foreign keys
  main_me_id = Column(Integer, ForeignKey('monitor_elements.id'), nullable=False)
  main_me = relationship("MonitorElement", foreign_keys=[main_me_id])
  optional_me1_id = Column(Integer, ForeignKey('monitor_elements.id'))
  optional_me1 = relationship("MonitorElement", foreign_keys=[optional_me1_id])
  optional_me2_id = Column(Integer, ForeignKey('monitor_elements.id'))
  optional_me2 = relationship("MonitorElement", foreign_keys=[optional_me2_id])

  __table_args__ = (UniqueConstraint('run', 'lumi', 'subsystem', 'dataset', name='_run_lumi_subsystem_dataset_uc'),)

class MonitorElement(base):
  __tablename__ = 'monitor_elements'

  id = Column(Integer, primary_key=True, nullable=False)
  run = Column(Integer, nullable=False)
  lumi = Column(Integer, nullable=False)
  me_path = Column(String, nullable=False)
  dataset = Column(String, nullable=False)
  eos_path = Column(String, nullable=False)
  me_blob = Column(Binary, nullable=False)
  gui_url = Column(String, nullable=False)
  image_url = Column(String, nullable=False)

  __table_args__ = (UniqueConstraint('run', 'lumi', 'me_path', 'dataset', name='_run_lumi_plotpath_dataset_uc'),)

class OMSDataCache(base):
  __tablename__ = 'oms_data_cache'

  id = Column(Integer, primary_key=True, nullable=False)
  run = Column(Integer, nullable=False)
  lumi = Column(Integer, nullable=False)
  start_time = Column(DateTime, nullable=False)
  end_time = Column(DateTime, nullable=False)
  
  b_field = Column(Float, nullable=False)
  energy = Column(Float, nullable=False)
  
  init_lumi = Column(Float, nullable=False)
  end_lumi = Column(Float, nullable=False)
  recorded_lumi = Column(Float, nullable=False)
  l1_key = Column(String, nullable=False)
  hlt_key = Column(String, nullable=False)
  l1_rate = Column(Float, nullable=False)
  hlt_physics_rate = Column(Float, nullable=False)
  duration = Column(Integer, nullable=False)
  fill_number = Column(Integer, nullable=False)
  injection_scheme = Column(String, nullable=False)
  era = Column(String, nullable=False)

def setup_db():
  base.metadata.create_all(db)

def get_session():
  Session = sessionmaker(db)
  session = Session()
  return session

if __name__ == '__main__':
  setup_db()
