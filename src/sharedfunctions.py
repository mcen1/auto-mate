#!/bin/env python3
import os
import re
import socket
import subprocess
import requests
import urllib3
import ssl
import shlex
import csv
from dbops import *
from accessops import *

WEBSITE_URL=os.environ["WEBSITE_URL"]
TEXTFILE_BASE="/usr/portal/supporting_tools/textfiles/"
RECORDKEEPINGFILE="/opt/pvc/recordkeeping/"
try:
  TEST_MODE=os.environ["TEST_MODE"]
except:
  TEST_MODE=False

def writeToRecordKeeper(filename,towrite):
  os.makedirs(RECORDKEEPINGFILE, exist_ok=True)
  with open(f"{RECORDKEEPINGFILE}{filename}", 'a+') as f:
    f.write(towrite)

def wrap_luckysevens(html_content):
    pattern = re.compile(r'(<div class="luckysevens">)(.*?)(</div>)', re.DOTALL)

    def wrap_text(match):
        # Extract the opening tag, content, and closing tag
        opening_tag, content, closing_tag = match.groups()

        # Wrap each character with <span> and animation-delay
        wrapped_content = ''.join(
            f'<span style="animation-delay: {i * 0.1}s">{char}</span>'
            for i, char in enumerate(content)
        )

        # Return the updated div with wrapped content
        return f"{opening_tag}{wrapped_content}{closing_tag}"

    # Perform the replacement
    return pattern.sub(wrap_text, html_content)

def getJobJSON():
  data=[]
  for file in glob.glob(f"{JSON_FILES_DIR}/*.json"):
    with open(file,encoding='UTF-8') as f:
      datafromfile=json.load(f)
      datafromfile["filename"]=file
      data.append(datafromfile)
  return data


def specialHtmlThing(mystring):
  toreturn=mystring
  toreturn=toreturn.replace('&lt;br&gt;','<br>')
  toreturn=toreturn.replace('&lt;blinkme&gt;','<div class=blinkme>').replace('&lt;/blinkme&gt;','</div>')
  toreturn=toreturn.replace('&lt;copycodeme&gt;','<div class="code-container codeme"><button class="copy-button">Copy</button><pre class="code-block"><code>').replace('&lt;/copycodeme&gt;','</code></pre></div>')
  toreturn=toreturn.replace('&lt;codeme&gt;','<div class="code-container codeme"><pre class="code-block"><code>').replace('&lt;/codeme&gt;','</code></pre></div>')
  # link parser
  pattern=r'&lt;link&gt;(.*?)&lt;/link&gt;'
  toreturn=re.sub(pattern,r"<a target='_blank' href='\1'>\1</a>",toreturn)
  # neon parser
  toreturn=toreturn.replace('&lt;neonme&gt;','<div class=neonme>').replace('&lt;/neonme&gt;','</div>')
  # 3d parser
  toreturn=toreturn.replace('&lt;luckysevensme&gt;','<div class="luckysevens">').replace('&lt;/luckysevensme&gt;','</div>')
  toreturn=wrap_luckysevens(toreturn)
  return toreturn

def shellSanitizer(commandtosanitize):
  badchars=[';','!','?','*',"'",'"','&']
  for badchar in badchars:
    commandtosanitize.replace(badchar,'')
  return commandtosanitize

# Function to ping an address
def pingSomething(address):
  user_param = shlex.quote(address)
  user_param = shellSanitizer(user_param)
  proc = subprocess.run( ["ping", "-W", "1", "-c", "1", user_param], shell=False)
  return proc.returncode

# Function to do an nslookup
def nslookupSomething(address):
  user_param = shlex.quote(address)
  user_param = shellSanitizer(user_param)
  proc = subprocess.run( ["nslookup", user_param], shell=False)
  return proc.returncode


# Look up if host is in DNS via socket.gethostbyname
def socketLookup(address):
  user_param = shlex.quote(address)
  user_param = shellSanitizer(user_param)
  ip_address = socket.gethostbyname(address)
  return ip_address

# Prevents XSS attacks
def urlSanitizer(userurl):
  badchars={">": "BAD&gt;","<": "BAD&lt;"}
  print(f"userurl is {userurl}")
  for chara in badchars:
    userurl.replace(chara,badchars[chara])
  if not userurl.startswith('/'):
    print(f"returning {WEBSITE_URL}")
    return WEBSITE_URL
  return WEBSITE_URL+userurl

# Function to check user's session in db
def checkUserSession(sessionid):
  sessionvalid=checkDBSession(sessionid)
  username=retrieveDBData(sessionid,"username")
  if sessionid==None or sessionvalid==False:
    return "invalid_session"
  if username==None:
    return "username_not_found_in_db"
  return "ok"

# Function to check what permissions a user has
def checkUserJobPerms(sessionid,username,jobname):
  if TEST_MODE:
    if username=="testlowpriv":
      return False
    return True
  userjobs=getUserJobsByGroup(sessionid)
#  print(f'{sessionid} by {username} is trying to run {jobname}...')
  if jobname not in userjobs:
    print(f'{username} is not allowed to run {jobname}.')
    return False
#  print(f'{username} is allowed to run {jobname}.')
  return True

# Search 'term' in 'filename'. Fuzzy is wildcarded.
def getSearchTermFromFile(filenumber,term,fuzzy):
  # use a filemapping map so the user can't probe OS files, only specify integers corresponding
  # to allowed files
  filemapping={"1":f"{TEXTFILE_BASE}snowapps.txt","2":f"{TEXTFILE_BASE}snowgroup1c379e996f166a401dd50ee9ea3ee42c.txt"}
  filetoget=filemapping[filenumber]
  if str(fuzzy).lower()=="true":
    fuzzy=True
  else:
    fuzzy=False
  maxrez=5
  my_file = open(filetoget, "r")
  data = my_file.read().split("\n")
  term=term.lower()
  toreturn=[]
  if len(term)<3:
    return []
#  print(f"searching {term} in {filetoget} fuzzy is {fuzzy}")
  for line in data:
    if line.lower().startswith(term.lower()) and fuzzy:
      toreturn.append(line)
      if len(toreturn)>=maxrez:
        return toreturn
    if line.lower()==term.lower() and not fuzzy:
      return [line]
  return toreturn

# Gil adapter for Github compat
class CustomHttpAdapter (requests.adapters.HTTPAdapter):
  '''Transport adapter" that allows us to use custom ssl_context.'''

  def __init__(self, ssl_context=None, **kwargs):
    self.ssl_context = ssl_context
    super().__init__(**kwargs)

  def init_poolmanager(self, connections, maxsize, block=False):
    self.poolmanager = urllib3.poolmanager.PoolManager(
      num_pools=connections, maxsize=maxsize,
      block=block, ssl_context=self.ssl_context)

# Get file from Github
def get_github_raw(org, file_path):
  urllib3.disable_warnings()
  token = f'Bearer {os.environ["GITHUB_TOKEN"]}'
  headers = {
    "Accept": "application/vnd.github.raw",
    "Authorization": token
  }
  url = f'https://raw.githubusercontent.com/{org}/{file_path}'

  ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
  ctx.options |= 0x4
  ctx.check_hostname = False
  session = requests.Session()
  session.mount('https://', CustomHttpAdapter(ctx))

  r = session.get(url, headers=headers, verify=False)
  file_content = (r.content).decode('utf-8')
  return file_content

def getJobRunStats():
  csv_file_path = f"{RECORDKEEPINGFILE}/jobruns.csv"
  jobs_by_month = {}
  with open(csv_file_path, newline='') as csvfile:
      reader = csv.reader(csvfile)
      for row in reader:
          if len(row) != 3:
              continue  # Skip malformed lines
          username, jobname, jobrundate = row
          try:
              key = f"{jobrundate.split('-')[0]}-{jobrundate.split('-')[1]}"
              if key not in jobs_by_month:
                jobs_by_month[key]=[]
              jobs_by_month[key].append(f"{username.strip()},{jobname.strip()},{jobrundate.strip()}")
          except ValueError:
              print(f"Skipping invalid date: {jobrundate}")

  jobs_by_month = dict(sorted(jobs_by_month.items(), reverse=True))
  return jobs_by_month
