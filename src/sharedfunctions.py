#!/bin/env python3
from dbops import *
from accessops import *
import os
import re
import socket

WEBSITE_URL=os.environ["WEBSITE_URL"]

def pingSomething(address):
  response = os.system('ping -W 1 -c 1 ' + address + ' > /dev/null 2>&1' )
  return response

def nslookupSomething(address):
  response = os.system('nslookup ' + address + ' > /dev/null 2>&1' )
  return response

def socketLookup(address):
  ip_address = socket.gethostbyname(address)
  return ip_address


def urlSanitizer(userurl):
  print(f"userurl is {userurl}")
  if not userurl.startswith('/'):
    print(f"returning {WEBSITE_URL}")
    return WEBSITE_URL
  return WEBSITE_URL+userurl

def checkUserSession(sessionid):
  sessionvalid=checkDBSession(sessionid)
  username=retrieveDBData(sessionid,"username")
  if sessionid==None or sessionvalid==False:
    return "invalid_session"
  if username==None:
    return "username_not_found_in_db"
  return "ok"

def checkUserJobPerms(sessionid,username,jobname):
  userjobs=getUserJobsByGroup(sessionid)
  print(f'{sessionid} by {username} is trying to run {jobname}...')
  if jobname not in userjobs:
    print(f'{username} is not allowed to run {jobname}.')
    return False
  print(f'{username} is allowed to run {jobname}.')
  return True



def getSearchTermFromFile(filename,term,fuzzy):
  if str(fuzzy).lower()=="true":
    fuzzy=True
  else:
    fuzzy=False
  maxrez=5
  if filename!="snowapps":
    return []
  my_file = open(f"/usr/portal/supporting_tools/textfiles/{filename}.txt", "r")
  data = my_file.read().split("\n")
  term=term.lower()
  toreturn=[]
  if len(term)<3:
    return []
  for line in data:
    if line.lower().startswith(term.lower()) and fuzzy:
      toreturn.append(line)
      if len(toreturn)>=maxrez:
        return toreturn
    if line.lower()==term.lower() and not fuzzy:
      return [line]
  return toreturn

#print(getSearchTermFromFile('snowapps','ans'))
