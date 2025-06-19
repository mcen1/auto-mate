#!/bin/env python3
""" AWX related routes go into this file """
import json
import os
import re
from flask import request,render_template,redirect, url_for,make_response
from markupsafe import Markup, escape
from runCHANGEMEpi import *
from app import app
from accessops import *
from dbops import *
from sharedfunctions import *

DISABLED_AWX_JOBS=os.getenv("DISABLED_AWX_JOBS",default="").split(",")
DISABLED_ENDPOINTS=os.getenv("DISABLED_ENDPOINTS",default="").split(",")

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

with open('universalfilter.json') as f:
  universalfilter = json.load(f)

# example  http://localhost:5000/runjobawxreqconf?
# awx-job-name=automation-awx-jobtesting-job&
# extravarfavoritecolor=aaa&extravarfavoriteanimal=bbbb
@app.route('/runjobawxreqconf', methods=["GET"])
def post_url_to_awx2():
  """ Run AWX job via url params. Conf means confirmation, the user needs to say yes """
  #print(f"Request to runjob is: {request.args}")
  if not request.args:
    return render_template('error.html',
                           data="No arguments sent to URL.",
                           errorcode=400,
                           URLPREFACE=URLPREFACE)
  sessionid=escape(request.cookies.get('sessionid'))
  session_sanitized=getAndReturnSession(sessionid)

  assjobparams=""
  #print(f"request.args is {request.args.to_dict()}")
  for item in request.args.to_dict():
    assjobparams=assjobparams+item+"="+request.args[item]+"&"
  if session_sanitized=="notfound":
    return render_template('login.html',
                           redirecturl=f"{URLPREFACE}/runjobawxreqconf?{assjobparams}",
                           URLPREFACE=URLPREFACE,
                           userinfo=f"Log in to continue to runjobawxreqconf?{assjobparams}.")
  try:
    jobname=request.args['awx-job-name']
  except Exception:
    return render_template('errorrunningjob.html',
                           jobdata="Mandatory parameter awx-job-name not specified")
  # check if this job is allowed to be ran via url (this is governed by the json file's run-via list)
  if jobname not in getJobsRanByURL():
    ez=f"This job is not allowed to be ran via this method. {jobname} not in {getJobsRanByURL()}"
    return render_template('error.html',data=ez,errorcode=403,URLPREFACE=URLPREFACE), 403
  username=retrieveDBData(sessionid,"username")
  canrun=checkUserJobPerms(sessionid,username,jobname)
  if not canrun:
    return render_template('error.html',
                           data=f"{username} is not in a group that is allowed to access this job",
                           errorcode=403,
                           URLPREFACE=URLPREFACE), 403
  print("attempting render template")
  expiry=renewDBSession(session_sanitized)
  itemrendertemplate="runjobconfirm.html"
  jobjson=getJobJSON()
  for jorb in jobjson:
    if jorb['awx-job-name']==jobname:
      jobmetadata=jorb
    
  print(f"{jobname.lower()} in {DISABLED_AWX_JOBS}")
  if jobname.lower() in DISABLED_AWX_JOBS or jobmetadata['portal-endpoint'].lower() in DISABLED_ENDPOINTS:
    itemrendertemplate="disabled.html"
  resp=make_response(render_template(itemrendertemplate,
                                     reqargs=request.args.to_dict(),
                                     jobmetadata=jobmetadata,
                                     URLPREFACE=URLPREFACE))
  resp.set_cookie('sessionid',
                  session_sanitized,
                  httponly=True,
                  secure=COOKIE_SECURITY,
                  samesite='Lax',
                  expires=expiry)
  return resp


# example http://localhost:5000/runjobawxreq?awx-job-name=
# automation-awx-jobtesting-job&extravarfavoritecolor=aaa&
# extravarfavoriteanimal=bbbb
# run job without confirmation dialog
@app.route('/runjobawxreq', methods=["GET"])
def post_url_to_awx():
  """ Run AWX job via URL without prompting for a yes/no from the user """
  #print(f"Request to runjob is: {request.args}")
  if not request.args:
    return render_template('error.html',
                           data="No arguments sent to URL.",
                           errorcode=400,
                           URLPREFACE=URLPREFACE)
  sessionid=escape(request.cookies.get('sessionid'))
  session_sanitized=getAndReturnSession(sessionid)
  assjobparams=""
  #print(f"request.args is {request.args.to_dict()}")
  for item in request.args.to_dict():
    assjobparams=assjobparams+item+"="+request.args[item]+"&"
  if session_sanitized=="notfound":
    return render_template('login.html',
                           redirecturl=f"{URLPREFACE}/runjobawxreq?{assjobparams}",
                           URLPREFACE=URLPREFACE,
                           userinfo=f"Please log in to continue to runjobawxreq?{assjobparams}.")
  try:
    jobname=request.args['awx-job-name']
  except Exception:
    return render_template('errorrunningjob.html',
                           jobdata="There was an error launching the job. Mandatory parameter awx-job-name not specified")
  # check if this job is allowed to be ran via url (this is governed by the json file's run-via list)
  if jobname not in getJobsRanByURL():
    return render_template('error.html',
                           data=f"This job is not allowed to be ran via this method. {jobname} not in {getJobsRanByURL()}",
                           errorcode=403,
                           URLPREFACE=URLPREFACE), 403
  username=retrieveDBData(sessionid,"username")
  canrun=checkUserJobPerms(sessionid,username,jobname)
  if not canrun:
    return render_template('error.html',
                           data=f"{username} is not in a group that is allowed to access this job",
                           errorcode=403,
                           URLPREFACE=URLPREFACE), 403
  print(f"Attempting to run via CHANGEMEpi {username} is username and request form is {request.form} ")
  usermeta=retrieveDBData(sessionid,"usermeta")
  if jobname.lower() in DISABLED_AWX_JOBS:
    return render_template('disabled.html',
                           data=f"Job has been disabled",
                           errorcode=403,
                           URLPREFACE=URLPREFACE), 403
  job_id=runCHANGEMEPIJob(request.args,username,{},usermeta)
  jobsan=job_id
  try:
    jobsan=json.loads(job_id)
    if "errors" in jobsan:
      if "credentials" in jobsan["errors"]:
        print(f"Real output hidden from user. Job output was {job_id}")
        jobsan["errors"]["credentials"]="Error setting credentials for job run."
  except Exception as ex:
    print(f"Exception putting output to json: {ex}")
  if "results" in job_id:
    jobida=json.loads(job_id)
    return redirect(f"{URLPREFACE}"+url_for('follow_on_awx', jobid=jobida["results"]))
  return render_template('errorrunningjob.html',
                         jobdata=f"There was an error launching the job. Received this reply when trying to launch: {jobsan}",
                         URLPREFACE=URLPREFACE)


# Run a job via a post from the human-interactive form
@app.route('/runjobawx', methods=["POST"])
def post_to_awx():
  """ Runs a job with user-supplied params to AWX """
  print(f"Request to runjob is: {request.form}")
  sessionid=escape(request.cookies.get('sessionid'))
  session_sanitized=getAndReturnSession(sessionid)

  username=retrieveDBData(sessionid,"username")
  if session_sanitized=="notfound":
    return render_template('login.html',
                           redirecturl=f"{URLPREFACE}/",
                           userinfo="Please log in with your CHANGEME Active Directory account.")
  usermeta=retrieveDBData(sessionid,"usermeta")
  # give error if nothing sent via post
  if not request.form:
    return render_template('error.html',
                           data="No arguments were sent via post.",
                           errorcode=400,
                           URLPREFACE=URLPREFACE)
  jobname=escape(request.form['awx-job-name'])
#  print(f"{sessionid} {username} is trying to run {jobname}...")
  # check if user can run this job
  canrun=checkUserJobPerms(sessionid,username,jobname)
  if not canrun:
    return render_template('error.html',
                           data=f"{username} is not in a group that is allowed to access this job",
                           errorcode=403,
                           URLPREFACE=URLPREFACE), 403
  if jobname.lower() in DISABLED_AWX_JOBS:
    return render_template('disabled.html',
                           data=f"Job has been disabled",
                           errorcode=403,
                           URLPREFACE=URLPREFACE), 403
  job_id=runCHANGEMEPIJob(request.form,username,{},usermeta)
  jobsan=job_id
  try:
    jobsan=json.loads(job_id)
    if "errors" in jobsan:
      if "credentials" in jobsan["errors"]:
        print(f"Real output hidden from user. Job output was {job_id}")
        jobsan["errors"]["credentials"]="Error setting credentials for job run."
  except Exception as ex:
    print(f"Exception putting output to json: {ex}")
  if "results" in job_id:
    jobida=json.loads(job_id)
    return redirect(f"{URLPREFACE}"+url_for('follow_on_awx', jobid=jobida["results"]))
  return render_template('errorrunningjob.html',
                         jobdata=f"There was an error launching the job. Received this reply when trying to launch: {jobsan}",
                         URLPREFACE=URLPREFACE)

@app.route('/canceljobawx', methods=["POST"])
def cancel_job_awx():
  """ Cancel an AWX job """
  sessionid=escape(request.cookies.get('sessionid'))
  session_sanitized=getAndReturnSession(sessionid)

  if not request.form:
    return {"error": "No params were sent to this url."}
  if session_sanitized=="notfound":
    return {"error":"session is invalid."}
  try:
    jobname=getJobName(escape(request.form["jobid"]))
  except Exception as ex:
    return {"error": f"There was an error launching the job. Received this reply when trying to launch: {ex}"}
  username=retrieveDBData(sessionid,"username")

  canrun=checkUserJobPerms(sessionid,username,jobname)
  if not canrun:
    return render_template('error.html',
                           data=f"{username} is not in a group that is allowed to access this job",
                           errorcode=403,
                           URLPREFACE=URLPREFACE), 403
  if jobname.lower() in DISABLED_AWX_JOBS:
    return render_template('disabled.html',
                           data=f"Job has been disabled",
                           errorcode=403,
                           URLPREFACE=URLPREFACE), 403
  job_data=cancelJobCHANGEMEPI({"job_id": escape(request.form["jobid"])})
  jobresults=json.loads(job_data)
  return render_template('cancelawxjob.html',jobdata=jobresults,URLPREFACE=URLPREFACE)

@app.route('/awxjobresultstatus', methods=["GET"])
def get_awx_job_status():
  """ Get job result status job log with HTML """
  sessionid=escape(request.cookies.get('sessionid'))
  session_sanitized=getAndReturnSession(sessionid)
  if not request.args:
    return {"error": "No params were sent to this url."}
  if session_sanitized=="notfound":
    return {"error":"session is invalid."}
  try:
    jobname=getJobName(escape(request.args["jobid"]))
  except Exception as ex:
    return {"error": f"There was an error launching the job. Received this reply when trying to launch: {ex}"}
  username=retrieveDBData(sessionid,"username")
  canrun=checkUserJobPerms(sessionid,username,jobname)
  if not canrun:
    return render_template('error.html',
                           data=f"{username} is not in a group that is allowed to access this job",
                           errorcode=403,
                           URLPREFACE=URLPREFACE), 403
  job_data=getJobStatus(escape(request.args["jobid"]))
  return job_data.replace("successful","finished")

# getJobsByTemplateName
@app.route('/awxtemplatejobs', methods=["GET"])
def get_awx_template_jobs():
  """ Get job result status job log with HTML """
  sessionid=escape(request.cookies.get('sessionid'))
  session_sanitized=getAndReturnSession(sessionid)
  if not request.args:
    return {"error": "No params were sent to this url."}
  if session_sanitized=="notfound":
    return {"error":"session is invalid."}
  try:
    jobname=escape(request.args["jobname"])
  except Exception as ex:
    return {"error": f"There was an error launching the job. Received this reply when trying to launch: {ex}"}
  username=retrieveDBData(sessionid,"username")
  canrun=checkUserJobPerms(sessionid,username,jobname)
  if not canrun:
    return render_template('error.html',
                           data=f"{username} is not in a group that is allowed to access this job",
                           errorcode=403,
                           URLPREFACE=URLPREFACE), 403
  jobjson=getJobJSON()
  for jorb in jobjson:
    if jorb['awx-job-name']==jobname:
      jobmetadata=jorb
  if 'disallow-logs' in jobmetadata and jobmetadata['disallow-logs']:
    return render_template('contentunavailable.html',job_name=jobname,URLPREFACE=URLPREFACE)
  job_data=getJobsByTemplateName(jobname)
  return render_template('joblogs.html',job_name=jobname,job_data=job_data,URLPREFACE=URLPREFACE)

# This is a text-only version of the job's output
# to facilitate the end user viewing the log and not overwhelming with requests
@app.route('/awxjobabridged', methods=["GET"])
def follow_on_awx_ajax():
  """ Get job result status json """
  sessionid=escape(request.cookies.get('sessionid'))
  session_sanitized=getAndReturnSession(sessionid)
  if not request.args:
    return {"error": "No params were sent to this url."}
  if session_sanitized=="notfound":
    return {"error":"session is invalid."}
  try:
    jobname=getJobName(escape(request.args["jobid"]))
  except Exception as ex:
    return {"error": f"There was an error launching the job. Received this reply when trying to launch: {ex}"}
  username=retrieveDBData(sessionid,"username")

  canrun=checkUserJobPerms(sessionid,username,jobname)
  if not canrun:
    return render_template('error.html',
                           data=f"{username} is not in a group that is allowed to access this job",
                           errorcode=403,
                           URLPREFACE=URLPREFACE), 403
  job_data=getOutputCHANGEMEPI(escape(request.args["jobid"]),"html")
  job_data=json.loads(job_data)
  logfilter=getJobLogFilters(jobname)
  jobresults=job_data["results"]
  # per-job specific filtering
  for replacement in universalfilter['eliminate_lines']:
    jobresults=jobresults.replace(replacement,'')
  if logfilter:
    if "replacements" in logfilter:
      for replacement in logfilter["replacements"]:
        jobresults=jobresults.replace(replacement['to_replace'],replacement['replacement'])
    if "regex_replacements" in logfilter:
      for replacement in logfilter["regex_replacements"]:
        jobresults=re.sub(replacement['to_replace'],replacement['replacement'], jobresults)
  tosay=specialHtmlThing(jobresults)
  return tosay

# This is the human-friendly log output page called after a job is executed
@app.route('/awxviewjob', methods=["GET"])
def follow_on_awx():
  """ View job run webpage renderer"""
  if not request.args:
    return render_template('error.html',
                           data="No parameters were sent in your request.",
                           URLPREFACE=URLPREFACE,
                           errorcode=400)
  sessionid=escape(request.cookies.get('sessionid'))
  session_sanitized=getAndReturnSession(sessionid)
  try:
    jobname=getJobName(escape(request.args["jobid"]))
  except Exception as ex:
    return render_template('errorrunningjob.html',
                           URLPREFACE=URLPREFACE,
                           jobdata=f"There was an error launching the job: {ex}")
  jobid=escape(request.args["jobid"])
  if session_sanitized=="notfound":
    return render_template('login.html',
                           URLPREFACE=URLPREFACE,
                           redirecturl=f"{URLPREFACE}/awxviewjob?jobid={jobid}",
                           userinfo=f"Please log in to continue to /awxviewjob?jobid={jobid}.")
  username=retrieveDBData(sessionid,"username")
  canrun=checkUserJobPerms(sessionid,username,jobname)
  if not canrun:
    return render_template('error.html',
                           data=f"{username} is not in a group that is allowed to access this job",
                           errorcode=403,
                           URLPREFACE=URLPREFACE), 403
  expiry=renewDBSession(session_sanitized)
  resp=make_response(render_template('viewrunjob.html',jobid=jobid,URLPREFACE=URLPREFACE))
  resp.set_cookie('sessionid',
                  session_sanitized,
                  httponly=True,
                  secure=COOKIE_SECURITY,
                  samesite='Lax',
                  expires=expiry)
  return resp
