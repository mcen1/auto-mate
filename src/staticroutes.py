#!/bin/env python3
""" Static routes that aren't app specific """
import os
from flask import request,render_template,redirect, make_response,send_from_directory
from markupsafe import Markup, escape
from runCHANGEMEpi import *
from app import app
from accessops import *
from dbops import *
from awxroutes import *
from sharedfunctions import *
import datetime

try:
  # set environment variable to "/portal" for k8s
  ROOT_DIR=os.environ["PORTALROOTDIR"]
except:
  ROOT_DIR=""
try:
  DOMAIN=os.environ["DOMAIN"]
except:
  DOMAIN="CHANGEME"
try:
  LOCALDEV=os.environ["LOCALDEV"]
except:
  LOCALDEV="no"
try:
  URLPREFACE=os.environ["URLPREFACE"]
except:
  URLPREFACE=""

COOKIE_SECURITY=True
if LOCALDEV=="yes":
  COOKIE_SECURITY=False

@app.route('/',methods=["GET"])
# Index of main page
def render_index():
  """ Renders index of main page """
  sessionid=escape(request.cookies.get('sessionid'))
  userlinks2=getUserJobFriendlyLinks(sessionid)
  # any failure of these operations imply an expired session
  session_sanitized=getAndReturnSession(sessionid)
  if session_sanitized=="notfound":
    return render_template('login.html', redirecturl=f"{URLPREFACE}/",URLPREFACE=URLPREFACE)
  try:
    extuserlinks=retrieveDBData(sessionid,'extlinks').split(',')
    linkstoshow=getLinkInfo(extuserlinks)
  except Exception as ex:
    print(f"Exception in index {ex} user session may be expired.")
    return render_template('login.html',
                           redirecturl=f"{URLPREFACE}/",
                           userinfo="Please log in with your CHANGEME Active Directory account.",
                           URLPREFACE=URLPREFACE)
  username=retrieveDBData(session_sanitized,"username")
  expiry=renewDBSession(session_sanitized)
  resp=make_response(render_template('index.html',
                                     userlinks=userlinks2,
                                     username=username,
                                     extlinks=linkstoshow,
                                     URLPREFACE=URLPREFACE))
  resp.set_cookie('sessionid',
                  session_sanitized,
                  httponly=True,
                  secure=COOKIE_SECURITY,
                  samesite='Lax',
                  expires=expiry)
  return resp

@app.after_request
# Implemented to address penetration testing recommendations
# Adds these headers to all responses to the client
def apply_client_headers(response):
  """ Apply headers to client response """
  response.headers["X-Frame-Options"] = "SAMEORIGIN"
  response.headers["X-Content-Type-Options"] = "nosniff"
  response.headers["Cache-Control"] = "no-store,no-cache"
  response.headers["Pragma"] = "no-cache"
  response.headers["X-XSS-Protection"] = "1; mode=block"
  response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
  csp = (
      "default-src 'self'; "
      "script-src 'self'; " 
      "script-src-elem 'self'; "
      "style-src 'self' 'unsafe-inline'; " 
      "img-src 'self'; "
      "font-src 'self';"
      "connect-src 'self';"
      "frame-src 'self'; "
      "object-src 'none'; "
      "base-uri 'self'; "
      "form-action 'self'; "
  )
  response.headers["Content-Security-Policy"] = csp
  return response

@app.route('/favicon.ico')
# Supplies favicon to client
def favicon():
  """ Create favicon """
  return send_from_directory(os.path.join(app.root_path, 'static'),
                             'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/refreshsession',methods=["GET"])
# Method to refresh user session based on activity such as clicking pages
# or following a job
def refresh_session():
  """ Refresh user session """
  sessionid=escape(request.cookies.get('sessionid'))
  session_sanitized=getAndReturnSession(sessionid)
  if session_sanitized=="notfound":
    return render_template('login.html', redirecturl=f"{URLPREFACE}/",URLPREFACE=URLPREFACE)
  expiry=renewDBSession(session_sanitized)
  resp=make_response(render_template('renewsession.html',URLPREFACE=URLPREFACE))
  resp.set_cookie('sessionid',
                  session_sanitized,
                  httponly=True,
                  secure=COOKIE_SECURITY,
                  samesite='Lax',
                  expires=expiry)
  return resp

@app.route('/checksession',methods=["GET"])
# Sends back whether or not session is valid
def check_session():
  """ Check user session """
  sessionid=escape(request.cookies.get('sessionid'))
  session_sanitized=getAndReturnSession(sessionid)
  if session_sanitized=="notfound":
    return {"results":"invalid"}
  expiry=getDBSession(session_sanitized)
  #resp=make_response({"response":"refreshed"})
  return {"results": expiry}

@app.route('/login',methods=["GET"])
# Log in the user
def render_login():
  """ Render login page """
  redirecturl=f"{URLPREFACE}/"
  errors=""
  if "redirecturl" in request.args:
    redirecturl=request.args["redirecturl"]
    redirecturl=urlSanitizer(redirecturl)
    print(f"redirecturl called, {redirecturl}")
  if "errors" in request.args:
    errors=request.args["errors"]
  return render_template('login.html',
                         redirecturl=redirecturl,
                         errors=errors,
                         URLPREFACE=URLPREFACE)

@app.route('/searchtext', methods=["POST"])
# Method to search a file for a string of text. Used for the SNOW apps for Infoblox job
def search_text_helper():
  """ Search a file for text """
  sessionid=escape(request.cookies.get('sessionid'))
  session_sanitized=getAndReturnSession(sessionid)
  if not request.json:
    return {"error": "No params were sent to this url."}
  if session_sanitized=="notfound":
    return {"error":"session is invalid."}
  filenumber=str(escape(request.json["filenumeric"]))
  searchrez=[]
  try:
    searchstring=escape(request.json["searchterm"])
    fuzzy=escape(request.json["fuzzy"])
    searchrez=getSearchTermFromFile(filenumber,searchstring,fuzzy)
  except Exception as ex:
    print(f"Exception caught in text helper: {ex}")
    return {"results": f"There was an error searching. Error was: {ex}"}
  return {"results": searchrez}

@app.route('/pingsomething', methods=["GET"])
# Pings an IP/host and returns the results
def ping_something_helper():
  """ Ping an IP or hostname """
  sessionid=escape(request.cookies.get('sessionid'))
  session_sanitized=getAndReturnSession(sessionid)
  if not request.args:
    return {"error": "No params were sent to this url."}
  if session_sanitized=="notfound":
    return {"error":"session is invalid."}
  address=escape(request.args["address"])
  pingrez={}
  try:
    pingrez=pingSomething(address)
  except Exception as ex:
    return {"results": f"There was an error pinging. Error was: {ex}"}
  return {"results": pingrez}

@app.route('/getagendpoint', methods=["GET"])
# getCHANGEMEEndpoint
def get_ag_endpoint_url():
  """ Get an CHANGEME endpoint """
  sessionid=escape(request.cookies.get('sessionid'))
  session_sanitized=getAndReturnSession(sessionid)
  if not request.args:
    return {"error": "No params were sent to this url."}
  if session_sanitized=="notfound":
    return {"error":"session is invalid."}
  endpointurl=escape(request.args["endpointurl"])
  pingrez={}
  try:
    endpointrez=getCHANGEMEEndpoint(endpointurl)
  except Exception as ex:
    return {"results": f"There was an error requesting endpoint. Error was: {ex}"}
  return endpointrez

@app.route('/socketlookup', methods=["GET"])
# Sends socket info back to client
def socket_something_helper():
  """ Socket lookup of hostname """
  sessionid=escape(request.cookies.get('sessionid'))
  session_sanitized=getAndReturnSession(sessionid)
  if not request.args:
    return {"error": "No params were sent to this url."}
  if session_sanitized=="notfound":
    return {"error":"session is invalid."}
  address=escape(request.args["address"])
  pingrez={}
  try:
    pingrez=socketLookup(address)
  except Exception as ex:
    return {"results": f"There was an error with the lookup. Error was: {ex}"}
  return {"results": pingrez}

@app.route('/dologin', methods=["POST"])
# Actually do the login
def dologin_and_redirect():
  """ Login user and redirect them to the page they were going or home """
  redirecturl=f"{URLPREFACE}/"
  usermeta={}
  if not request.form:
    print("Nothing found in request form.")
    return render_template('login.html',
                           data="No arguments sent via post.",
                           errorcode=400,
                           redirecturl=redirecturl,
                           URLPREFACE=URLPREFACE)
  if "redirecturl" in request.form:
    redirecturl=request.form["redirecturl"]
    redirecturl=urlSanitizer(redirecturl)
    print(f"redirecturl called from dologin, {redirecturl}")
  try:
    username=escape(request.form['ldusername'])
    password=str(request.form['ldpassword'])
  except Exception as ex:
    return render_template('login.html',errors=ex,redirecturl=redirecturl,URLPREFACE=URLPREFACE)
  try:
    usergroups=loginUserLDAP(username,password,DOMAIN)
    usermeta=ldapUserMeta(username,password,DOMAIN)
  except Exception as ex:
    return render_template('login.html',errors=ex,redirecturl=redirecturl,URLPREFACE=URLPREFACE)
  print(f"Assembling endpoints for {username}...")
  allowedjobsandendpoints=populateUserJobsAndEndpoints(usergroups)
  # db stores this data as comma-separated string, need to convert it to a python list via join
  allowedjobs=','.join(allowedjobsandendpoints[0])
  allowedendpoints=','.join(allowedjobsandendpoints[1])
  allowedlinks=','.join(allowedjobsandendpoints[2])
  dbinfo=createUserDBSession(username,allowedjobs,allowedendpoints,allowedlinks,usermeta)
  newsessionid=dbinfo[0]
  expiry=dbinfo[1]
  if redirecturl in ('', '/'):
    if URLPREFACE!="" and URLPREFACE not in redirecturl:
      redirecturl=URLPREFACE+"/"

  print(f"redirecting {username} to '{redirecturl}'")
  resp = make_response(redirect(redirecturl, code=302))
  writeToRecordKeeper("logins.csv",f"{username},{datetime.datetime.now()}\n")
  resp.set_cookie('sessionid',
                  newsessionid,
                  httponly=True,
                  secure=COOKIE_SECURITY,
                  samesite='Lax',
                  expires=expiry)
  return resp

@app.route('/logout', methods=["GET"])
# Log the user out and destroy the session in the db
def do_logout():
  """ Log user out """
  sessionid=escape(request.cookies.get('sessionid'))
  session_sanitized=getAndReturnSession(sessionid)
  if session_sanitized!="notfound":
    deleteDBSession(sessionid)
  redirecturl=f"{URLPREFACE}/"
  if "redirecturl" in request.args:
    redirecturl=request.args["redirecturl"]
    redirecturl=urlSanitizer(redirecturl)
  resp=make_response(redirect('/',code=302))
  resp.set_cookie('sessionid', '', expires=0,httponly=True,secure=COOKIE_SECURITY,samesite='Lax')
  return resp

@app.route('/health', methods=["GET"])
# Healthcheck endpoint
def do_gethealth():
  """ Healthcheck for k8s """
  try:
    dbhealth=dbGetHealth()
  except Exception as ex:
    return {"health": "dbunhealthy", "error": ex}
  try: 
    CHANGEMEpihealth=getCHANGEMEPIHealth()
  except Exception as ex:
    return {"health": "CHANGEMEpiunhealthy", "error": ex}
  return {"dbhealth": dbhealth, "CHANGEMEpihealth": CHANGEMEpihealth}

@app.route('/repolookup', methods=["GET"])
# Look up github repository
def repo_lookup_helper():
  """ Repo lookup function """
  sessionid=escape(request.cookies.get('sessionid'))
  session_sanitized=getAndReturnSession(sessionid)
  if session_sanitized=="notfound":
    return {"error":"session is invalid."}
  repo_org=escape(request.args["repo_org"])
  repo_file_path=escape(request.args["repo_file_path"])
  results={}
  try:
    results=get_github_raw(org=repo_org,file_path=repo_file_path)
  except Exception as ex:
    return {"results": f"There was an error retrieving content. Error was: {ex}"}
  return {"results": results}

@app.route('/checkAutomateEnv',methods=["GET"])
# Retrieve what environment CHANGEME is running in
def check_automate_environment():
  """ Retrieve environment CHANGEME is running on """
  sessionid=escape(request.cookies.get('sessionid'))
  session_sanitized=getAndReturnSession(sessionid)
  if session_sanitized=="notfound" or 'AUTOMATE_ENVIRONMENT' not in os.environ:
    return {"results":"invalid"}
  return {"results":os.environ['AUTOMATE_ENVIRONMENT']}

@app.route('/updateuserpageview',methods=["GET"])
def update_user_page_env():
  sessionid=escape(request.cookies.get('sessionid'))
  session_sanitized=getAndReturnSession(sessionid)
  pageescaped=escape(request.args["page"])
  action="view"
  usernamesviewing=updateSessionViewTable(session_sanitized,pageescaped,action)
  return {"results": usernamesviewing}

@app.route('/jobrunstats',methods=["GET"])
# Method to refresh user session based on activity such as clicking pages
# or following a job
def get_job_run_stats():
  """ Refresh user session """
  sessionid=escape(request.cookies.get('sessionid'))
  session_sanitized=getAndReturnSession(sessionid)
  if session_sanitized=="notfound":
    return render_template('login.html', redirecturl=f"{URLPREFACE}/",URLPREFACE=URLPREFACE)
  expiry=renewDBSession(session_sanitized)
  jobrunstats=getJobRunStats()
  resp=make_response(render_template('jobrunstats.html',URLPREFACE=URLPREFACE,jobrunstats=jobrunstats))
  resp.set_cookie('sessionid',
                  session_sanitized,
                  httponly=True,
                  secure=COOKIE_SECURITY,
                  samesite='Lax',
                  expires=expiry)
  return resp

@app.route('/jobrunstats.csv')
def send_jobrunstats_txt():
    # Using request args for path will expose you to directory traversal attacks
    return send_from_directory('/opt/pvc/recordkeeping', 'jobruns.csv')
