#!/bin/bash
CONTAINERNAME=$(basename "`pwd`")
docker build -t $CONTAINERNAME .

