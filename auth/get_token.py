import requests
import json
from dotenv import dotenv_values
import os
import sys

env_variables = dotenv_values(os.path.dirname(__file__) + "/.env")

headers = {"content-type": "application/x-www-form-urlencoded"}


def exchange_tokens(token):
    data = {
        "client_id": env_variables["CLIENT_ID"],
        "client_secret": env_variables["CLIENT_SECRET"],
        "audience": env_variables["AUDIENCE"],
        "grant_type": "urn:ietf:params:oauth:grant-type:token-exchange",
        "requested_token_type": "urn:ietf:params:oauth:token-type:access_token",
        "subject_token": token,
    }
    data = requests.post(
        url=env_variables["AUTH_SERVICE_URL"], data=data, headers=headers
    )

    try:
        data_ = data.json()
        access_token = data_["access_token"]
        return access_token

    except Exception as e:
        return "Error: " + str(e)


def get_token():
    data = {
        "client_id": env_variables["CLIENT_ID"],
        "client_secret": env_variables["CLIENT_SECRET"],
        "audience": env_variables["AUDIENCE"],
        "grant_type": "client_credentials",
    }

    data = requests.post(
        url=env_variables["AUTH_SERVICE_URL"], data=data, headers=headers
    )
    try:
        data_ = data.json()
        access_token = data_["access_token"]
        data_access_token = exchange_tokens(access_token)
        return data_access_token

    except Exception as e:
        return "Error: " + str(e)
