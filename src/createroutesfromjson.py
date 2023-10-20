#!/bin/env python3
import glob
import os
import json

data=[]
os.chdir("json")
for file in glob.glob("*.json"):
  with open(file) as f:
    datafromfile=json.load(f)
    datafromfile["filename"]=file
    data.append(datafromfile)

header="""
from flask import Flask,request,render_template,jsonify,redirect, url_for,abort,make_response
import json
from runmiddleware import *
from app import app
from accessops import *
from sharedfunctions import *
try:
  LOCALDEV=os.environ["LOCALDEV"]
except:
  LOCALDEV="no"
try:
  URLPREFACE=os.environ["URLPREFACE"]
except:
  URLPREFACE=""
cookiesecurity=True
if LOCALDEV=="yes":
  cookiesecurity=False

"""
#URLPREFACE="URLPREFACE"
tosay=header+"\n"
ITOAPI_URL=os.environ["ITOAPI_URL"]
for item in data:
  mydatum=f"""
@app.route('/{item['portal-endpoint']}')
def render_{item['portal-endpoint'].replace('-','_')}():
  sessionid=request.cookies.get('sessionid')
  sessioncheckresults=checkUserSession(sessionid)
  if sessioncheckresults!="ok":
    return render_template('login.html',URLPREFACE=URLPREFACE, redirecturl=f"{{URLPREFACE}}/{item['portal-endpoint']}",userinfo="Please log in with your ABC Active Directory account to continue to {item['portal-endpoint']}.")

  username=retrieveDBData(sessionid,"username")
  canrun=checkUserJobPerms(sessionid,username,"{item['awx-job-name']}")
  if canrun == False:
    return render_template('awxerror.html',URLPREFACE=URLPREFACE,errorcode="403",errordata=f"Error: {{username}} is not in a group that can view this job.")
  f = open('json/{item['filename']}')
  jobdata = json.load(f)
  f.close()
  expiry=renewDBSession(sessionid)
  resp=make_response(render_template('{item['job-type']}job.html',URLPREFACE=URLPREFACE,jobdata=jobdata,username=username))
  resp.set_cookie('sessionid', sessionid, httponly=True, secure=cookiesecurity, samesite='Lax',expires=expiry)
  return resp
"""
  tosay=tosay+mydatum+"\n"

print(tosay)
