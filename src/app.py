import json
from flask import Flask,request,render_template,jsonify,redirect, url_for
from runCHANGEMEpi import *
from os import *
import sys
from flask_wtf.csrf import CSRFProtect
app = Flask(__name__)
app.config.update(
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SECRET_KEY=os.getenv("RANDOM_SECRET_KEY"),
    SERVER_NAME=os.getenv("SERVER_NAME"),
    SESSION_COOKIE_NAME=os.getenv("SESSION_COOKIE_NAME")
)

try:
  TEST_MODE=os.environ["TEST_MODE"]
except:
  TEST_MODE=False

if 'TEST_MODE' not in os.environ:
  print(f"Running with CSRF")
  csrf = CSRFProtect()
  csrf.init_app(app)
else:
  if 'AB_K8S_NODE_NAME' in os.environ and 'TEST_MODE' in os.environ:
    print(f"\n----------\nCannot run in kubernetes with test mode enabled. Quitting!\n----------\n")
    app=None
  print(f"Running without CSRF")

import staticroutes
import sys
sys.path.insert(0, os.path.abspath('genroutes'))
import autogeneratedroutes


if __name__ == '__main__':
  app.run(use_reloader=True)
