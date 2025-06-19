#!/bin/env python3
""" db operations go in this file """
import sqlite3
import os
import datetime
import secrets
from markupsafe import Markup, escape


def makeTokens(mysize):
  """ make tokens url safe """
  return secrets.token_urlsafe(mysize)

try:
  DB_FILE=os.environ["DB_FILE"]
except:
  DB_FILE="/usr/portal/appdatabase/database.db"

try:
  TEST_MODE=os.environ["TEST_MODE"]
except:
  TEST_MODE=False

SESSION_IDLE=15

def getTimeFromNow(sessiontime):
  """ return time from now to generate expiry """
  current_time = datetime.datetime.now()  # use datetime.datetime.utcnow() for UTC time
  expiry = current_time + datetime.timedelta(minutes=sessiontime)
  return int(expiry.timestamp())

def getAllSessions():
  allsessions={}
  """ show db sessions """
  conn = sqlite3.connect(DB_FILE)
  c = conn.cursor()
  sql="SELECT sessionid FROM sessions"
  sqlvars=()
  c.execute(sql,sqlvars)
  myres=c.fetchall()
  conn.close()
  for session in myres:
    allsessions[session[0]]=session[0]
  return allsessions 

def getAndReturnSession(session_id):
  if TEST_MODE:
    if session_id=="testlowpriv":
        return "testlowpriv"
    return "TESTMODE"
  allsessions=getAllSessions()
  try:
    mysession=allsessions[escape(session_id)]
  except:
    return "notfound"
  return mysession

def showDB():
  """ show db sessions """
  conn = sqlite3.connect(DB_FILE)
  c = conn.cursor()
  sql="SELECT * FROM sessions"
  sqlvars=()
  c.execute(sql,sqlvars)
  myres=c.fetchall()
  conn.close()
  return myres

def deleteDBSession(session_id):
  """ deletes session from db """
  allsessions=getAllSessions()
  try:
    mysession=allsessions[session_id]
  except:
    return False
  conn = sqlite3.connect(DB_FILE)
  c = conn.cursor()
  sql="SELECT username FROM sessions where sessionid = ?"
  sqlvars=(mysession,)
  c.execute(sql,sqlvars)
  myres=c.fetchone()
  print(f"myres is {myres}")
  if myres:
    usernametodel=myres[0]
    print(f"deleting all sessions for username {usernametodel}")
    sql="DELETE FROM sessions WHERE username = ?"
    sqlvars=(usernametodel,)
    c.execute(sql,sqlvars)
    conn.commit()
  conn.close()
  return True

def checkDBSession(session_id):
  """ check database session for info """
  allsessions=getAllSessions()
  print(f"session_id is {session_id} ")
  try:
    mysession=allsessions[session_id]
  except Exception as ex:
    print(f"{session_id} not found in db! ex is {ex} checkDBSession {allsessions}")
    return False
  conn = sqlite3.connect(DB_FILE)
  c = conn.cursor()
  sql="SELECT expires,jobs FROM sessions where sessionid = ?"
  sqlvars=(mysession,)
  c.execute(sql,sqlvars)
  relevantsessions=c.fetchone()
  if relevantsessions is None:
    print("No session found")
    conn.close()
    return False
  expiry=int(relevantsessions[0])
  jobs=relevantsessions[1]
  if int(expiry)<int(datetime.datetime.now().timestamp()):
    print("User session has expired")
    deleteDBSession(mysession)
    conn.close()
    return False
  conn.close()
  return jobs

def getDBSession(session_id):
  """ return db session validity """
  allsessions=getAllSessions()
  if TEST_MODE:
    return "valid"
  try:
    mysession=allsessions[session_id]
  except:
    print(f"{session_id} not found in db! getDBSession")
    return "invalid"
  conn = sqlite3.connect(DB_FILE)
  c = conn.cursor()
  sql="SELECT expires,jobs FROM sessions where sessionid = ?"
  sqlvars=(mysession,)
  c.execute(sql,sqlvars)
  relevantsessions=c.fetchone()
  if relevantsessions is None:
    print("No session found")
    conn.close()
    return "invalid"
  expiry=int(relevantsessions[0])
  if int(expiry)<int(datetime.datetime.now().timestamp()):
    print(f"User session for {mysession} has expired")
    deleteDBSession(mysession)
    conn.close()
    return "invalid"
  conn.close()
  return "valid"



def retrieveDBData(session_id,toget):
  """ return toget from db """
  if TEST_MODE and session_id=="testlowpriv":
    if toget=="username":
      print(f"low privilege user set and TEST_MODE is active")
      return "testlowpriv"
  validgets={'username':'username','usermeta':'usermeta','endpoints':'endpoints','jobs':'jobs','sessionid':'sessionid','extlinks':'extlinks'}
  if toget not in validgets:
    print(f"{session_id} did an invalid request for column {toget} in retrieveDBData!")
    return None
  allsessions=getAllSessions()
  try:
    mysession=allsessions[session_id]
  except:
    print(f"{session_id} not found in db! retrieveDBData")
    return None
  conn = sqlite3.connect(DB_FILE)
  c = conn.cursor()
  sql=f"SELECT {validgets[toget]} FROM sessions where sessionid = ?"
  #sql="SELECT ? FROM sessions where sessionid = ?"
  sqlvars=(mysession,)
  c.execute(sql,sqlvars)
  relevantsessions=c.fetchone()
  #print(f"Returning relevantsessions: {relevantsessions[0]}")
  conn.close()
  if relevantsessions is None:
    print(f"No relevant session found for {session_id}")
    return None
  return relevantsessions[0]

def retrieveDBUsers():
  """ retrieve username and expires from sessions """
  conn = sqlite3.connect(DB_FILE)
  c = conn.cursor()
  sql="SELECT username,expires FROM sessions"
  sqlvars=()
  c.execute(sql,sqlvars)
  relevantsessions=c.fetchall()
  conn.close()
  if relevantsessions is None:
    return None
  return relevantsessions

def dbDumpAll():
  """ dump db data """
  conn = sqlite3.connect(DB_FILE)
  c = conn.cursor()
  sql="SELECT * FROM sessions"
  sqlvars=()
  c.execute(sql,sqlvars)
  relevantsessions=c.fetchall()
  conn.close()
  return relevantsessions

def dbGetHealth():
  """ database health check """
  try:
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    sql="BEGIN;"
    sqlvars=()
    c.execute(sql,sqlvars)
    c.execute("COMMIT;",sqlvars)
    conn.close()
    return "goodhealth"
  except Exception as e:
    return f"badhealth {e}"
  #print(f"Returning relevantsessions: {relevantsessions[0]}")



def createUserDBSession(username,jobs,endpoints,extlinks,usermeta):
  """ create user session in db """
#  print(f"usermeta is {usermeta}")
  expiry=getTimeFromNow(SESSION_IDLE)
  session_id=makeTokens(32)
  conn = sqlite3.connect(DB_FILE)
  c = conn.cursor()
  sql="INSERT INTO sessions (sessionid,username,jobs,expires,endpoints,extlinks,usermeta) VALUES(?,?,?,?,?,?,?)"
  sqlvars=(session_id,username,jobs,expiry,endpoints,extlinks,usermeta)
  c.execute(sql,sqlvars)
  conn.commit()
  conn.close()
  print(f"Created session")
  return (session_id,expiry)

def renewDBSession(session_id):
  """ renew session """
  if TEST_MODE:
    return ""
  allsessions=getAllSessions()
  mysession=allsessions[session_id]
#  print(f"call to renew {mysession}")
  expiry=getTimeFromNow(SESSION_IDLE)
  conn = sqlite3.connect(DB_FILE)
  c = conn.cursor()
  sql="UPDATE sessions SET expires = ? WHERE sessionid=?"
  sqlvars=(expiry, mysession)
  c.execute(sql,sqlvars)
  conn.commit()
#  print(f"{mysession} renewed!")
  return expiry

def updateSessionViewTable(sessionid,page,action):
  conn = sqlite3.connect(DB_FILE)
  c = conn.cursor()
  # Assume users who haven't updated expiry have left the page
  sql=f"DELETE from pageviews WHERE expires < {int(datetime.datetime.now().timestamp())}"
  c.execute(sql)
  conn.commit()
  relevantusernames=[]
  if action=="view":
    # Get list of valid endpoints the session can see
    sql=f"SELECT endpoints FROM sessions where sessionid='{sessionid}'"
    sqlvars=()
    c.execute(sql,sqlvars)
    relevantjob=c.fetchall()
    specialpage=page
    # Logic for the special way runjobawxreqconf is triggered
    if page.startswith('runjobawxreqconf?'):
      stringtosearch=page.replace('runjobawxreqconf?','')
      myresult = {}
      # Split keypairs to determine what job the user is trying to run
      for pair in stringtosearch.split('&'):
        key, value = pair.split('=')
        myresult[key] = value
      try:
        # Ends with -job, get rid of it
        specialpage=myresult['awx-job-name'].replace('-job','')
      except Exception as e:
        print(f"Exception in parsing for viewers: {ex}")
        return "Invalid page"
    # Only show page viewers for pages the user can access
    if specialpage not in relevantjob[0][0].split(','):
       return "Invalid page"
    sql=f"SELECT username FROM sessions where sessionid='{sessionid}'"
    sqlvars=()
    c.execute(sql,sqlvars)
    relevantusernames=c.fetchall()
    for user in relevantusernames:
      expiry=getTimeFromNow(1)
      userpagego=page+user[0]
      sql="INSERT OR REPLACE INTO pageviews (userpagego,page,user,expires) VALUES(?,?,?,?)"
      sqlvars=(userpagego,page,user[0],expiry)
      c.execute(sql,sqlvars)
      conn.commit()
    # Finally, return what users are currently viewing the same page
    sql=f"SELECT user FROM pageviews where page='{page}'"
    sqlvars=()
    c.execute(sql,sqlvars)
    relevantusernames=c.fetchall()
  conn.close()
  return relevantusernames

def setupDB():
  """ instantiate database """
  print("setting up db...")
  conn = sqlite3.connect(DB_FILE)
  c = conn.cursor()

  c.execute('''
          CREATE TABLE IF NOT EXISTS sessions
          ([sessionid] TEXT PRIMARY KEY, [username] TEXT, [jobs] TEXT, [expires] TEXT, [endpoints] TEXT, [extlinks] TEXT, [usermeta] TEXT)
          ''')
  c.execute("CREATE TABLE IF NOT EXISTS pageviews([userpagego] TEXT PRIMARY KEY, [page] TEXT, [user] TEXT, [expires] TEXT)")
  conn.commit()
  conn.close()

if __name__ == '__main__':
  setupDB()

