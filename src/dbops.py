#!/bin/env python3
import sqlite3
from sqlite3 import Error
import os
import datetime
import uuid
import secrets


def makeTokens(mysize):
  return secrets.token_urlsafe(mysize)  

try:
  DB_FILE=os.environ["DB_FILE"]
except:
  DB_FILE="/usr/portal/appdatabase/database.db"
SESSION_IDLE=15

def getTimeFromNow():
  current_time = datetime.datetime.now()  # use datetime.datetime.utcnow() for UTC time
  expiry = current_time + datetime.timedelta(minutes=SESSION_IDLE)
  return int(expiry.timestamp())

def showDB():
  conn = sqlite3.connect(DB_FILE)
  c = conn.cursor()
  sql="SELECT * FROM sessions"
  vars=()
  c.execute(sql,vars)
  myres=c.fetchall()
  conn.close()
  return myres

def deleteDBSession(session_id):
  conn = sqlite3.connect(DB_FILE)
  c = conn.cursor()
  sql="SELECT username FROM sessions where sessionid = ?"
  vars=(session_id,)
  #sql="DELETE FROM sessions WHERE sessionid = ?"
  #vars=(session_id,)
  c.execute(sql,vars)
  myres=c.fetchone()
  print(f"myres is {myres}")
  if myres:
    usernametodel=myres[0]
    print(f"deleting all sessions for username {usernametodel}")
    sql="DELETE FROM sessions WHERE username = ?"
    vars=(usernametodel,)
    c.execute(sql,vars)
    conn.commit()
  conn.close()
  return True

def checkDBSession(session_id):
  conn = sqlite3.connect(DB_FILE)
  c = conn.cursor()
  sql="SELECT expires,jobs FROM sessions where sessionid = ?"
  vars=(session_id,)
  c.execute(sql,vars)
  relevantsessions=c.fetchone()
#  print(f"relevant sessions: {relevantsessions}")
  if relevantsessions == None:
    print("No session found")
    conn.close()
    return False
  expiry=int(relevantsessions[0])
  jobs=relevantsessions[1]
  if int(expiry)<int(datetime.datetime.now().timestamp()):
    print(f"User session for session_id has expired")
    deleteDBSession(session_id)
    conn.close()
    return False
#  if expiry>=int(datetime.datetime.now().timestamp()):
#    renewDBSession(session_id)
  conn.close()
  return jobs

def getDBSession(session_id):
  conn = sqlite3.connect(DB_FILE)
  c = conn.cursor()
  sql="SELECT expires,jobs FROM sessions where sessionid = ?"
  vars=(session_id,)
  c.execute(sql,vars)
  relevantsessions=c.fetchone()
#  print(f"relevant sessions: {relevantsessions}")
  if relevantsessions == None:
    print("No session found")
    conn.close()
    return "invalid"
  expiry=int(relevantsessions[0])
  jobs=relevantsessions[1]
  if int(expiry)<int(datetime.datetime.now().timestamp()):
    print(f"User session for session_id has expired")
    deleteDBSession(session_id)
    conn.close()
    return "invalid"
  conn.close()
  return "valid"



def retrieveDBData(session_id,toget):
  conn = sqlite3.connect(DB_FILE)
  c = conn.cursor()
  sql=f"SELECT {toget} FROM sessions where sessionid = ?"
  vars=(session_id,)
  c.execute(sql,vars)
  relevantsessions=c.fetchone()
  #print(f"Returning relevantsessions: {relevantsessions[0]}")
  conn.close()
  if relevantsessions==None:
    return None
  return relevantsessions[0]

def dbDumpAll():
  conn = sqlite3.connect(DB_FILE)
  c = conn.cursor()
  sql=f"SELECT * FROM sessions"
  vars=()
  c.execute(sql,vars)
  relevantsessions=c.fetchall()
  #print(f"Returning relevantsessions: {relevantsessions[0]}")
  conn.close()
  return relevantsessions

def dbGetHealth():
  try:
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    sql=f"BEGIN;"
    vars=()
    c.execute(sql,vars)
    c.execute("COMMIT;",vars)
    conn.close()
    return "goodhealth"
  except Exception as e:
    return f"badhealth {e}"
  #print(f"Returning relevantsessions: {relevantsessions[0]}")



def createUserDBSession(username,jobs,endpoints,extlinks):
  expiry=getTimeFromNow()
  session_id=makeTokens(32)
  conn = sqlite3.connect(DB_FILE)
  c = conn.cursor()
  sql="INSERT INTO sessions (sessionid,username,jobs,expires,endpoints,extlinks) VALUES(?,?,?,?,?,?)"
  vars=(session_id,username,jobs,expiry,endpoints,extlinks)
  c.execute(sql,vars)
  conn.commit()
  conn.close()
  return (session_id,expiry)

def renewDBSession(session_id):
  print(f"call to renew {session_id}")
  expiry=getTimeFromNow()
  conn = sqlite3.connect(DB_FILE)
  c = conn.cursor()
  sql="UPDATE sessions SET expires = ? WHERE sessionid=?"
  vars=(expiry, session_id)
  c.execute(sql,vars)
  conn.commit()
  print(f"{session_id} renewed!")
  return expiry


def setupDB():
  print("setting up db...")
  conn = sqlite3.connect(DB_FILE) 
  c = conn.cursor()

  c.execute('''
          CREATE TABLE IF NOT EXISTS sessions
          ([sessionid] TEXT PRIMARY KEY, [username] TEXT, [jobs] TEXT, [expires] TEXT, [endpoints] TEXT, [extlinks] TEXT)
          ''')
  conn.commit()
  conn.close()

if __name__ == '__main__':
    setupDB()

