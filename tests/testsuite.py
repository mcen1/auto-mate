#!/bin/env python3
import traceback
import requests
import json
import sys

testsfailed=0

APP_PORT="8000"
APP_HOST="localhost"

def tallyResults(testgo,inverse=False):
#  print(f"{testgo}\n")
  if not inverse:
    if testgo['results']!="success":
      print("Failed!")
      return 1
    return 0
  else:
    if testgo['results']!="success":
      return 0
    print("Failed!")
    return 1
  return 0

def testURL(urlpath,payload,methodtype="post",cookies={}):
  try:
    if methodtype=="post":
      print(f"Sending {payload} to {urlpath}")
      x = requests.post(urlpath,data=payload,cookies=cookies)
    elif methodtype=="get":
      x = requests.get(urlpath,json=payload,cookies=cookies)
    y=x.text
    z=x.status_code
  except Exception as e:
    return {"results":"failed","log": traceback.format_exc()}
  return {"text": y, "status_code": z}


print(f"Testing if app is running locally on {APP_HOST}:{APP_PORT}")
testresult=testURL(f"http://{APP_HOST}:{APP_PORT}",{},methodtype="get")
if "Username" in testresult['text']:
  print("{'results':'success'}\n")
else:
  testsfailed=testsfailed+1
  print(f"Could not find app running on {APP_HOST}:{APP_PORT}. Quitting all tests!")
  sys.exit(255)

print(f"Testing {APP_HOST}:{APP_PORT}/health")
testresult=testURL(f"http://{APP_HOST}:{APP_PORT}/health",{},methodtype="get")
jsonresult=json.loads(testresult['text'])
badresults=0
for result in jsonresult:
  if jsonresult[result]!="goodhealth":
    testsfailed=testsfailed+1
    print(f"Healthcheck result: {results} is {jsonresult[result]}")
if badresults == 0:
  print("{'results':'success'}\n")
else:
  badresults=badresults+1

print(f"Testing if form is rendering properly http://{APP_HOST}:{APP_PORT}/runjobawxreqconf?awx-job-name=CHANGEME-job&extravarticket_number=CTASK012345&")
testresult=testURL(f"http://{APP_HOST}:{APP_PORT}/runjobawxreqconf?awx-job-name=CHANGEME-job&extravarticket_number=CTASK12345&",{},methodtype="get")
if "Are you sure you want to run" in testresult['text']:
  print("{'results':'success'}\n")
else:
  testsfailed=testsfailed+1
  print(f"Could not validate form is functional {APP_HOST}:{APP_PORT}/runjobawxreqconf?awx-job-name=CHANGEME-job&extravarticket_number=CTASK012345&. Looking for text 'Are you sure you want to run' and didn't find it.")
  print(f"testresult is {testresult}")

print(f"Testing if form is rendering properly http://{APP_HOST}:{APP_PORT}/automation_awx_APP_demo")
testresult=testURL(f"http://{APP_HOST}:{APP_PORT}/automation_awx_APP_demo",{},methodtype="get")
if "Demonstration" in testresult['text']:
  print("{'results':'success'}\n")
else:
  testsfailed=testsfailed+1
  print(f"Could not validate form is functional {APP_HOST}:{APP_PORT}/automation_awx_APP_demo. Looking for text 'Demonstration' and didn't find it.")
  print(f"testresult is {testresult}")

print(f"Testing if form is denying access properly for http://{APP_HOST}:{APP_PORT}/automation_awx_APP_demo")
testresult=testURL(f"http://{APP_HOST}:{APP_PORT}/automation_awx_APP_demo",{},methodtype="get",cookies={"sessionid":"testlowpriv"})
if testresult['status_code']==403:
  print("{'results':'success'}\n")
else:
  testsfailed=testsfailed+1
  print(f"Low privilege user can still access {APP_HOST}:{APP_PORT}/automation_awx_APP_demo. Looking for HTTP response 403 and did not receive it.")
  print(f"Received {testresult['status_code']}")

if '403' not in testresult['text']:
  testsfailed=testsfailed+1
  print(f"Low privilege tried to go to {APP_HOST}:{APP_PORT}/automation_awx_APP_demo. Looking for text '403' and didn't find it.")
  print(f"testresult is {testresult}")

# Post to URL
print(f"Testing if form POST is submitting properly using vars found for http://{APP_HOST}:{APP_PORT}/automation_awx_APP_demo")
postpayload={
  "awx-job-name": "project-APP_demos-job",
  "extravarrole_to_run": "varchecker",
  "extravarone_to_five": "1"
}
testresult=testURL(f"http://{APP_HOST}:{APP_PORT}/runjobawx",postpayload,methodtype="post")
if '<input type="hidden" id="jobid" name="jobid" value="' in testresult['text']:
  print("{'results':'success'}\n")
else:
  testsfailed=testsfailed+1
  print(f"Could not validate posting to form is functional {APP_HOST}:{APP_PORT}/runjobawx. Looking for text indicating a jobid was returned and didn't find it.")
  print(f"testresult is {testresult}")

print(f"Number of tests failed: {testsfailed}")
sys.exit(testsfailed)
