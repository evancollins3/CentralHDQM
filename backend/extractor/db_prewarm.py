#!/usr/bin/env python3

import os, sys
# Insert parent dir to sys.path to import db_access and cern_sso
sys.path.insert(1, os.path.realpath(os.path.pardir))
import db_access


def prewarm():
	# prewarm multiple times
	for _ in range(3):
		session = db_access.get_session()
		try:
			print('Prewarming...')
			response = session.execute("SELECT pg_prewarm('historic_data_points');")
			print('Done.')
		except Exception as e:
			print(e)
		finally:
			session.close()


if __name__ == '__main__':
  prewarm()