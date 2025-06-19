#!/bin/env python3
""" This file contains the logic behind who gets access to what and how. """
import os
import glob
import json
import ldap3
from dbops import *

LDAP_HOST=os.environ["LDAP_HOST"]
AUTOMATE_ENVIRONMENT=os.getenv("AUTOMATE_ENVIRONMENT",default="non-production")

try:
  LDAP_BASEDN=os.environ["LDAP_BASEDN"]
except:
  print("Error loading LDAP_BASEDN env var. \
        Defaulting to OU=CHANGEMEusers,DC=CHANGEME,DC=CHANGEME,DC=com")
  LDAP_BASEDN="OU=CHANGEMEusers,DC=CHANGEME,DC=CHANGEME,DC=com"

try:
  GROUP_BASE=os.environ["GROUP_BASE"]
except:
  print("Error loading GROUP_BASE env var. Defaulting to DC=CHANGEME,DC=CHANGEME,DC=com")
  GROUP_BASE="DC=CHANGEME,DC=CHANGEME,DC=com"
AUTO_BIND_NO_TLS=True

# Change this for local dev
JSON_FILES_DIR="/git/automation-portal-CHANGEME/src/json/"
try:
  JSON_FILES_DIR=os.environ["JSON_FILES_DIR"]
except:
  print("Error loading JSON_FILES_DIR env var. Defaulting to /usr/portal/json/")
  JSON_FILES_DIR="/usr/portal/json/"

EXTERNAL_LINKS_DIR="/git/automation-portal-CHANGEME/src/external_links/"
try:
  EXTERNAL_LINKS_DIR=os.environ["JSON_LINKS_DIR"]
except:
  print("Error loading JSON_LINKS_DIR env var. Defaulting to /usr/portal/external_links/")
  EXTERNAL_LINKS_DIR="/usr/portal/external_links/"

LOG_FILTERS_DIR="/git/automation-portal-CHANGEME/src/log_filters/"
try:
  LOG_FILTERS_DIR=os.environ["JSON_FILTERS_DIR"]
except:
  print("Error loading JSON_FILTERS_DIR env var. Defaulting to /usr/portal/log_filters/")
  LOG_FILTERS_DIR="/usr/portal/log_filters/"


if os.path.exists(JSON_FILES_DIR) is False:
  raise RuntimeError(f"{JSON_FILES_DIR} does not exist!")

if os.path.isdir(JSON_FILES_DIR) is False:
  raise RuntimeError(300,f"{JSON_FILES_DIR} is not a directory!")



def getJobLogFilters(jobname):
  """ gather job log filters for jobname """
  data=[]
  returndata={}
  for file in glob.glob(f"{LOG_FILTERS_DIR}*.json"):
    with open(file,encoding='UTF-8') as f:
      datafromfile=json.load(f)
      datafromfile["filename"]=file
      data.append(datafromfile)
  for item in data:
    if item["awx-job-name"] == jobname:
      if "replacements" in item:
        returndata["replacements"]=item["replacements"]
      if "regex_replacements" in item:
        returndata["regex_replacements"]=item["regex_replacements"]
  return returndata



def checkGroups(adgroups,jobgroups):
  """ check groups in LDAP """
  for aditem in adgroups:
    for jobitem in jobgroups:
      if jobitem.lower() == aditem.lower():
        return True
  return False

def populateUserJobsAndEndpoints(usergroups):
  """ retrieve user endpoints and jobs based on groups """
  data=[]
  for file in glob.glob(f"{JSON_FILES_DIR}*.json"):
    with open(file,encoding='UTF-8') as f:
      datafromfile=json.load(f)
      datafromfile["filename"]=file
      data.append(datafromfile)
#      print(f"added {datafromfile['filename']} for user")
  validjobs=[]
  validendpoints=[]
  for job in data:
    if checkGroups(usergroups,job['valid-ad-groups']) or 'everyone' in job['valid-ad-groups']:
      validjobs.append(job['awx-job-name'])
      validendpoints.append(job['portal-endpoint'])
  datalinks=[]
  print("checking links...")
  for file in glob.glob(f"{EXTERNAL_LINKS_DIR}*.json"):
    with open(file,encoding='UTF-8') as f:
      datafromfile=json.load(f)
      datafromfile["filename"]=file
      datalinks.append(datafromfile)
#      print(f"added {datafromfile['filename']} for user")
  validlinks=[]
  for extlink in datalinks:
    lnkgroups=extlink['valid-ad-groups']
    if checkGroups(usergroups,lnkgroups) or 'everyone' in lnkgroups:
      validlinks.append(extlink['name'])
  return (validjobs,validendpoints,validlinks)

def getLinkInfo(linkgroup):
  """ get link info and return as list """
  datalinks=[]
  toreturn=[]
  for file in glob.glob(f"{EXTERNAL_LINKS_DIR}*.json"):
    with open(file,encoding='UTF-8') as f:
      datafromfile=json.load(f)
      datafromfile["filename"]=file
      datalinks.append(datafromfile)
  for linkname in linkgroup:
    for extlink in datalinks:
      nameo=extlink['name']
      if nameo==linkname:
        toreturn.append(extlink)
  return toreturn


def getUserJobsByGroup(sessionid):
  """ Function to query our db for user's allowed jobs """
  try:
    jobshere=retrieveDBData(sessionid,"jobs")
    if jobshere is not None:
      return jobshere.split(",")
  except Exception as e:
    print(f"User getUserJobsByGroup db error: {e}")
  return False

def getJobsRanByURL():
  """ json files allowed jobs """
  allowedjobs=[]
  for file in glob.glob(f"{JSON_FILES_DIR}*.json"):
    with open(file,encoding='UTF-8') as f:
      datafromfile=json.load(f)
      try:
        if "url" in datafromfile['run-via']:
          allowedjobs.append(datafromfile['awx-job-name'])
      except:
        pass
  return allowedjobs

def allJobFiles():
  """ sends back all json files as list"""
  datafromfile=[]
  for file in glob.glob(f"{JSON_FILES_DIR}*.json"):
    with open(file,encoding='UTF-8') as f:
      datafromfile.append(json.load(f))
  return datafromfile

def getUserJobFriendlyLinks(sessionid):
  """ Get user friendly links """
  useroutput={}
  jobshere=retrieveDBData(sessionid,"endpoints")
  if jobshere is None:
    return False
  jobsan=jobshere.split(",")
  alljobs=allJobFiles()
  for job in jobsan:
    for item in alljobs:
      if "visibility" in item and item["visibility"]=="hidden":
        continue
      if "availability" in item and AUTOMATE_ENVIRONMENT != item["availability"] and item["availability"]!="all":
        continue
      icon="generic.png"
      if "tags" in item:
        tags=item["tags"]
      else:
        tags=[]
      if "icon" in item:
        icon=item["icon"]
      if item["portal-endpoint"]==job:
        if "category" in item:
          category=item["category"]
        else:
          category=""
        if "friendly-name" in item:
          friendlyname=item["friendly-name"]
        else:
          friendlyname=item["portal-endpoint"]
        endpoint=item["portal-endpoint"]
        shortdesc=""
        if "short-description" in item:
          shortdesc=item["short-description"]
        if category not in useroutput:
          useroutput[category]=[]
        useroutput[category].append({"friendlyname":friendlyname,
                                     "endpoint":endpoint,
                                     "short-description": shortdesc,
                                     "tags": tags,
                                     "icon": icon})
        useroutput[category]=sorted(useroutput[category], key=lambda x: x.get("friendlyname","").lower())
  return useroutput

# Function to query our db for user's endpoints
def getUserEndpointsByGroup(sessionid):
  """ get users allowed endpoints by their group membership """
  try:
    jobshere=retrieveDBData(sessionid,"endpoints")
    if jobshere is not None:
      return jobshere.split(",")
  except Exception as e:
    print(f"User getUserEndpointsByGroup jobs db error: {e}")
  return False

def loginUserLDAP(ldusername,ldpassword,domain):
  """ log in a user using credentials supplied """
  print(f"username is {ldusername}")
  print(f"Querying LDAP for {ldusername} groups...")
  conn = ldap3.Connection(ldap3.Server(LDAP_HOST, port=389, use_ssl=False),
    auto_bind=AUTO_BIND_NO_TLS, user=f"{ldusername}@{domain}",
    password=ldpassword)
  filter3=f'(&(sAMAccountName={ldusername}))'
  conn.search(search_base=GROUP_BASE,
    search_filter=filter3, search_scope="SUBTREE",
    attributes=['memberOf'], size_limit=0)
  response=json.loads(str(conn.response_to_json()))
  memberof=response['entries'][0]['attributes']['memberOf']
  return memberof

def ldapUserMeta(ldusername,ldpassword,domain):
  """ get user metadata from LDAP """
  print(f"Querying LDAP for {ldusername} meta...")
  conn = ldap3.Connection(ldap3.Server(LDAP_HOST, port=389, use_ssl=False),
    auto_bind=AUTO_BIND_NO_TLS, user=f"{ldusername}@{domain}",
    password=ldpassword)
  filter3=f'(&(sAMAccountName={ldusername}))'
  conn.search(search_base=GROUP_BASE,
    search_filter=filter3, search_scope="SUBTREE",
    #attributes=['*'], size_limit=0)
    attributes=['name',
                'displayName',
                'division',
                'department',
                'mail',
                'mobile',
                'title',
                'unixHomeDirectory',
                'manager'], size_limit=0)
  response=json.loads(str(conn.response_to_json()))
  usermeta=response['entries'][0]['attributes']
  usermeta["_automateassumedemail"]=str(ldusername.replace("_tr1","")+"@CHANGEME.com")
  #print(str(usermeta))
  return str(usermeta)



#print(allJobFiles())
