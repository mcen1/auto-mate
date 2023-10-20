#!/bin/env python3
import requests
import json
import time
import urllib3
import os
import datetime
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def lookupKey(keytofind):
#  print(f"Looking up {keytofind} in environment variables...")
#  if keytofind in os.environ:
#    print(f"Found {keytofind} in environment variables!")
#  else:
#    print(f"Couldn't find {keytofind} in environment variables. A default value might be used.")
  return os.environ.get(str(keytofind))

token=''
middleware_url=''
try:
  token=lookupKey('ITOAPI_TOKEN')
except Exception as e:
  print(f'ERROR: ITOAPI_TOKEN undefined! Cannot launch any AWX jobs. Error: {e}')
  token=''
if not token:
  print('ERROR: ITOAPI_TOKEN undefined! Cannot launch any AWX jobs.')
  token=''

headers={"Content-type": "application/json",'apikey': token}

try:
  middlewareurl=lookupKey('ITOAPI_URL')
except Exception as e:
  print(f'ERROR: ITOAPI_URL undefined environment variable. Cannot launch any AWX jobs. Error: {e}')
  middlewareurl=''
if not middlewareurl:
  print('ERROR: ITOAPI_URL is empty. Cannot launch any AWX jobs. {middlewareurl}')

try:
  certVerify = lookupKey('CERT_VERIFY')
except Exception as e:
  certVerify = '/etc/ssl/certs/ca-certificates.crt'

if not certVerify:
  certVerify = '/etc/ssl/certs/ca-certificates.crt'

if certVerify.lower()=="false":
  certVerify=False
certVerify=False

def postJobITOAPI(tosend):
  now = datetime.datetime.now()
  url=f"https://{middlewareurl}/middleware/api/v1/automation/awx_launch/launch_nowait"
  x = requests.post(url,json = tosend, verify=certVerify, headers=headers)
  job_output=x.text
  #print(json.dumps(json_output, indent=4))
  return job_output

def cancelJobITOAPI(tosend):
  now = datetime.datetime.now()
  url=f"https://{middlewareurl}/middleware/api/v1/automation/awx_launch/cancel_job"
  x = requests.post(url,json = tosend, verify=certVerify, headers=headers)
  job_output=x.text
  #print(json.dumps(json_output, indent=4))
  return job_output


def getJobName(jobID):
  now = datetime.datetime.now()
  url=f"https://{middlewareurl}/middleware/api/v1/automation/awx_launch/job_info"
  x = requests.post(url, json={"job_id": jobID}, verify=certVerify,headers=headers)
  job_output=json.loads(x.text)
  job_name=job_output['results']['name']
  #print(json.dumps(json_output, indent=4))
  return job_name

def getJobStatus(jobID):
  now = datetime.datetime.now()
  url=f"https://{middlewareurl}/middleware/api/v1/automation/awx_launch/job_status"
  x = requests.post(url, json={"job_id": jobID}, verify=certVerify,headers=headers)
  job_output=json.loads(x.text)
  job_status=job_output['results']['job_status']
  #print(json.dumps(json_output, indent=4))
  return job_status


def getOutputITOAPI(jobID,outputtype):
  now = datetime.datetime.now()
  url=f"https://{middlewareurl}/middleware/api/v1/automation/awx_launch/job_status_format"
  x = requests.post(url, json={"job_id": jobID,"output_format": outputtype}, verify=certVerify,headers=headers)
  job_output=x.text
  #print(json.dumps(json_output, indent=4))
  return job_output

def runITOAPIJob(userparams,username,extrastuff):
  if 'awx-job-name' not in userparams:
    print("error: parameters passed to runITOAPIJob are malformed.")
    return {"error": "parameters passed to runITOAPIJob are malformed."}
  extravars={"_ab_itoa_portal_meta_launched": True, "_ab_itoa_portal_meta_ranby": username, "_ab_itoa_portal_meta_jobname": userparams['awx-job-name']}
  jobtags=""
  skiptags=""
  # add extravars from form into posting
  for item in userparams:
    if item.startswith('extravar'):
      extravars[item.replace("extravar","")]=userparams[item]
  for item in extrastuff:
    print(f"adding {item} via extrastuff")
    extravars[item]=extrastuff[item]
  awxinstancegroups=[]
  jobcredential=[]
  if "awxinstancegroups" in userparams:
    awxinstancegroups=userparams.getlist("awxinstancegroups")
  if "awxjobcredentials" in userparams:
    jobcredential=userparams.getlist("awxjobcredentials")
  if "awxjobtags" in userparams:
    jobtags=userparams["awxjobtags"]
  if "awxjobskiptags" in userparams:
    skiptags=userparams["awxjobskiptags"]
  
  myjobparams={"job_name":userparams['awx-job-name'],"job_params": {"extra_vars":extravars, "job_tags":jobtags, "skip_tags": skiptags}}
  if len(jobcredential)>0:
    myjobparams["job_params"]["credentials"]=jobcredential
  if len(awxinstancegroups)>0:
    myjobparams["job_params"]["instance_groups"]=awxinstancegroups
  jobNumber=postJobITOAPI(myjobparams)
  now = datetime.datetime.now()
  print(f"{now} Jobnumber is: {jobNumber}")
  return jobNumber
