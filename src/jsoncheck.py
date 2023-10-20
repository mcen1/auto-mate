#!/usr/bin/env python3
import sys
import json
import glob

MYDIR=sys.argv[1]
def checkJSONFiles(mydir):
  data=[]
  for file in glob.glob(f"{mydir}/*.json"):
    with open(file) as f:
      print(f"Attempting to load file {file}")
      datafromfile=json.load(f)
  print(f"Validated .json files in {mydir}")
checkJSONFiles(MYDIR)
