#!/bin/env python3
from flask import Flask,request,render_template,jsonify,redirect, url_for,abort,make_response,send_from_directory
import json
from runmiddleware import *
from app import app
from accessops import *
from dbops import *
from awxroutes import *
from sharedfunctions import *
import os

try:
  # set environment variable to "/portal" for k8s
  rootdir=os.environ["PORTALROOTDIR"]
except:
  rootdir=""
try:
  DOMAIN=os.environ["DOMAIN"]
except:
  DOMAIN="company.com"
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

print(f"URLPREFACE defined as '{URLPREFACE}'")
@app.route('/',methods=["GET"])
def render_index():
  sessionid=request.cookies.get('sessionid')
  userlinks=getUserEndpointsByGroup(sessionid)
  userlinks2=getUserJobFriendlyLinks(sessionid)
  # any failure of these operations imply an expired session
  sessioncheckresults=checkUserSession(sessionid)
  if sessioncheckresults!="ok":
    return render_template('login.html', redirecturl=f"{URLPREFACE}/",URLPREFACE=URLPREFACE)
  try:
    extuserlinks=retrieveDBData(sessionid,'extlinks').split(',')
    linkstoshow=getLinkInfo(extuserlinks)
  except Exception as e:
    print(f"Exception in index {e} user session may be expired.")
    return render_template('login.html', redirecturl=f"{URLPREFACE}/",userinfo="Please log in with your ABC Active Directory account.",URLPREFACE=URLPREFACE)
  username=retrieveDBData(sessionid,"username")
  expiry=renewDBSession(sessionid)
  resp=make_response(render_template('index.html',userlinks=userlinks2,username=username,extlinks=linkstoshow,URLPREFACE=URLPREFACE))
  resp.set_cookie('sessionid', sessionid, httponly=True, secure=cookiesecurity, samesite='Lax',expires=expiry)
  return resp

@app.after_request
def apply_client_headers(response):
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Cache-Control"] = "no-store,no-cache"
    response.headers["Pragma"] = "no-cache"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/refreshsession',methods=["GET"])
def refresh_session():
  sessionid=request.cookies.get('sessionid')
  sessioncheckresults=checkUserSession(sessionid)
  if sessioncheckresults!="ok":
    return render_template('login.html', redirecturl=f"{URLPREFACE}/",URLPREFACE=URLPREFACE)
  username=retrieveDBData(sessionid,"username")
  expiry=renewDBSession(sessionid)
  #resp=make_response({"response":"refreshed"})
  resp=make_response(render_template('renewsession.html',URLPREFACE=URLPREFACE))
  resp.set_cookie('sessionid', sessionid, httponly=True, secure=cookiesecurity, samesite='Lax',expires=expiry)
  return resp

@app.route('/checksession',methods=["GET"])
def check_session():
  sessionid=request.cookies.get('sessionid')
  sessioncheckresults=checkUserSession(sessionid)
  if sessioncheckresults!="ok":
    return {"results":"invalid"}
  username=retrieveDBData(sessionid,"username")
  expiry=getDBSession(sessionid)
  #resp=make_response({"response":"refreshed"})
  return {"results": expiry}




@app.route('/login',methods=["GET"])
def render_login():
  redirecturl=f"{URLPREFACE}/"
  errors=""
  if "redirecturl" in request.args:
    redirecturl=request.args["redirecturl"]
    redirecturl=urlSanitizer(redirecturl)
  if "errors" in request.args:
    errors=request.args["errors"]
  return render_template('login.html', redirecturl=redirecturl,errors=errors,URLPREFACE=URLPREFACE)

@app.route('/searchtext', methods=["POST"])
def search_text_helper():
  sessionid=request.cookies.get('sessionid')
  sessioncheckresults=checkUserSession(sessionid)
  if not request.form:
    return {"error": "No params were sent to this url."}
  filetry=request.form["file"]
  if sessioncheckresults!="ok":
    return {"error":"session is invalid."}
  searchrez=[]
  try:
    searchstring=request.form["searchterm"]
    fuzzy=request.form["fuzzy"]
    searchrez=getSearchTermFromFile(filetry,searchstring,fuzzy)
    print(f"searchrez is {searchrez}")
  except Exception as e:
    return {"results": f"There was an error searching. Error was: {e}"}
  return {"results": searchrez}

@app.route('/pingsomething', methods=["GET"])
def ping_something_helper():
  sessionid=request.cookies.get('sessionid')
  sessioncheckresults=checkUserSession(sessionid)
  if not request.args:
    return {"error": "No params were sent to this url."}
  if sessioncheckresults!="ok":
    return {"error":"session is invalid."}
  address=request.args["address"]
  pingrez={}
  try:
    pingrez=pingSomething(address)
  except Exception as e:
    return {"results": f"There was an error pinging. Error was: {e}"}
  return {"results": pingrez}

@app.route('/socketlookup', methods=["GET"])
def socket_something_helper():
  sessionid=request.cookies.get('sessionid')
  sessioncheckresults=checkUserSession(sessionid)
  if not request.args:
    return {"error": "No params were sent to this url."}
  if sessioncheckresults!="ok":
    return {"error":"session is invalid."}
  address=request.args["address"]
  pingrez={}
  try:
    pingrez=socketLookup(address)
  except Exception as e:
    return {"results": f"There was an error with the lookup. Error was: {e}"}
  return {"results": pingrez}



@app.route('/dologin', methods=["POST"])
def dologin_and_redirect():
  redirecturl=f"{URLPREFACE}/"
  if not request.form:
    print(f"Nothing found in request form.")
    e="No arguments were sent via post."
    errorcode=400
    return render_template('login.html',data=e,errorcode=errorcode,redirecturl=redirecturl,URLPREFACE=URLPREFACE)
  if "redirecturl" in request.form:
    redirecturl=request.form["redirecturl"]
    redirecturl=urlSanitizer(redirecturl)
  try:
    username=request.form['ldusername']
    password=request.form['ldpassword']
  except Exception as e:
    return render_template('login.html',errors=e,redirecturl=redirecturl,URLPREFACE=URLPREFACE)
  try:
    usergroups=loginUserLDAP(username,password,DOMAIN)  
  except Exception as e:
    return render_template('login.html',errors=e,redirecturl=redirecturl,URLPREFACE=URLPREFACE)
  print(f"Assembling endpoints for {username}...")
  allowedjobsandendpoints=populateUserJobsAndEndpoints(usergroups)
  print(f"Creating session for user with params {username}:{allowedjobsandendpoints[0]}:{allowedjobsandendpoints[1]}:{allowedjobsandendpoints[2]}")
  # db stores this data as comma-separated string, need to convert it to a python list via join
  allowedjobs=','.join(allowedjobsandendpoints[0])
  allowedendpoints=','.join(allowedjobsandendpoints[1])
  allowedlinks=','.join(allowedjobsandendpoints[2])
  dbinfo=createUserDBSession(username,allowedjobs,allowedendpoints,allowedlinks)
  sessionid=dbinfo[0]
  expiry=dbinfo[1]
  print(f"Created session {sessionid} for {username}")
  if redirecturl=="" or redirecturl=="/":
    if URLPREFACE!="" and URLPREFACE not in redirecturl:
      redirecturl=URLPREFACE+"/"

  print(f"redirecting {username} to '{redirecturl}'")
  resp = make_response(redirect(redirecturl, code=302))
  resp.set_cookie('sessionid', sessionid, httponly=True, secure=cookiesecurity, samesite='Lax',expires=expiry)
  return resp

@app.route('/logout', methods=["GET"])
def do_logout():
  sessionid=request.cookies.get('sessionid')
  if sessionid!="":
    deleteDBSession(sessionid)
  redirecturl=f"{URLPREFACE}/"
  errors=""
  if "redirecturl" in request.args:
    redirecturl=request.args["redirecturl"]
    redirecturl=urlSanitizer(redirecturl)
  if "errors" in request.args:
    errors=request.args["errors"]
  resp=make_response(redirect('/',code=302))
  #resp=make_response(render_template('login.html', redirecturl=redirecturl,errors=errors,URLPREFACE=URLPREFACE))
  resp.set_cookie('sessionid', '', expires=0)
  return resp

#@app.route('/dump', methods=["GET"])
#def do_dump():
#  junk={}
#  for item in request.environ:
#    junk[item]=str(request.environ.get(item))
#  return junk

#@app.route('/nodeinfo', methods=["GET"])
#def do_nodeinfo():
#  mynode=os.getenv('AB_K8S_NODE_NAME')
#  myhost=os.getenv('HOSTNAME')
#  mymiddleware=os.getenv('ITOAPI_URL')
#  return {"node_name":mynode,"hostname":myhost,"middleware_url":mymiddleware}

@app.route('/health', methods=["GET"])
def do_gethealth():
  try:
    myhealth=dbGetHealth()
  except Exception as e:
    return {"health": "unhealthy", "error": e}
  return {"health": myhealth}

