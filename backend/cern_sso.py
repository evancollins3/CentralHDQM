import os

import requests
from urllib.parse import urlparse, urljoin
from xml.etree import ElementTree

def get_cookies(url, usercert, userkey, verify=False):
  """ Get CERN SSO cookies

      Args:
        url: CERN URL (https://cmsoms.cern.ch)
        usercert: full path to certificate file
        userkey: full path to certificate key file
        verify: should client verify host certificate (bool) or path to certificate (string)
  """

  with requests.Session() as session:
    session.cert = (usercert, userkey)

    # SSO redirects to Auth URL
    redirect = session.get(url, verify=verify)
    redirect.raise_for_status()

    # Auth URL        
    base = urljoin(redirect.url, "auth/sslclient/")
    query = urlparse(redirect.url).query
    auth_url = "{}?{}".format(base, query)

    # Auth response
    auth_resp = session.get(auth_url, verify=verify)
    auth_resp.raise_for_status()

    # Parse login form
    tree = ElementTree.fromstring(auth_resp.content)

    action = tree.findall("body/form")[0].get("action")
    form_data = dict(
        (
            (element.get("name"), element.get("value"))
            for element in tree.findall("body/form/input")
        )
    )
    
    session.post(url=action, data=form_data, verify=verify)

    return session.cookies
