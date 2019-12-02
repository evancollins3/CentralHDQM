import os, sys
sys.path.insert(1, os.path.realpath(os.path.pardir))
import db_access

def batch_iterable(iterable, chunksize=100):
  queue=[]
  for value in iterable:
    if len(queue) >= chunksize:
      yield queue
      queue = []
    queue.append(value)
  yield queue

# Executes a SQL transaction
def exec_transaction(sql, params=None):
  session = db_access.get_session()
  try:
    if type(sql) == list:
      for query in sql:
        session.execute(query, params)
    else:
      session.execute(sql, params)
    session.commit()
    return True
  except Exception as e:
    print(e)
    return False
  finally:
    session.close()

# Returns file names as a list from comma separated string
def get_all_me_names(names):
  names = names.split(',')
  names = [x.strip() for x in names if x]
  return names