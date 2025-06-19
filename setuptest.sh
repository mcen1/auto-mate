# set up a testing environment that will resemble what we end up creating
apk --no-cache add libcap dcron coreutils python3 py3-pip curl busybox-extras jq 
apk --no-cache add --virtual build-dependencies build-base python3-dev 
apk --no-cache add iputils 
pip3 install --upgrade  --break-system-packages pip 
pip3 install  --break-system-packages -r requirements.txt 
source .env
export DB_FILE=/tmp/app.db
# TEST_MODE allows for unauthenticated users to run any job.
# Only enable it for automated testing
export TEST_MODE=True
apk add git 
apk del build-dependencies 
cd src
python3 createroutesfromjson.py
python3 dbops.py
nohup gunicorn -w 4 -b 0.0.0.0:8000 wsgi:app &
# Run test suites
python3 ../tests/testsuite.py
