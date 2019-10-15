from __future__ import print_function
from sqlalchemy import create_engine  
from sqlalchemy import Column, String  
from sqlalchemy.ext.declarative import declarative_base  
from sqlalchemy.orm import sessionmaker

db_string = ''

db = create_engine(db_string)
base = declarative_base()

class HistoricData(base):
  __tablename__ = 'historic_data'

  id = Column(Integer, primary_key=True, nullable=False)
  run = Column(Integer, nullable=False)
  lumi = Column(Integer, nullable=False)
  name = Column(String, nullable=False)
  dataset = Column(String, nullable=False)
  pd = Column(String, nullable=False)

Session = sessionmaker(db)
session = Session()

base.metadata.create_all(db)
