#!/bin/env python3
# go to service now, retrieve all apps, store in text file
# to help users pick the right app
import requests
import os
from requests.auth import HTTPBasicAuth
import time
import urllib3
import json
import sys
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)



snusername = os.environ["SNOW_USERNAME"]
snpassword = os.environ["SNOW_PASSWORD"]
api_url = os.environ["SNOW_HOST"]
# how many entries per request in SNOW
snow_limits=5000

def getAllApps():
  snow_offset=0
  goteverything=False
  allapps=[]
  while goteverything!=True:
    url_base=f"/api/now/table/cmdb_ci_service_discovered?sysparm_offset={snow_offset}&sysparm_fields=name&sysparm_query=operational=1"
    headers = {"Content-Type":"application/json","Accept":"application/json"}

    response = requests.get(api_url+url_base, auth=(snusername, snpassword), headers=headers, verify=False )

    if response.status_code != 200:
        print('Status:', response.status_code, 'Headers:', response.headers, 'Error Response:',response.json())
        exit()
    data = response.json()
    if len(data['result'])==0:
      goteverything=True
      print("completed snow load")
    for item in data['result']:
      if item['name'] not in allapps:
        allapps.append(item['name'])
    snow_offset=snow_offset+snow_limits
    print(f"SNOW user accounts retrieved: {snow_offset}")
    time.sleep(5)
  return allapps 


def loadSnowAppsTxt(filetogo):
  doop=getAllApps()
  doop.sort()
  file = open(filetogo,'w')
  for item in doop:
  	file.write(item+"\n")
  file.close()
  print("Done loading SNOW apps")

loadSnowAppsTxt(sys.argv[1])
