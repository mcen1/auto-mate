This is where all the code is kept.

# Local database
You need to run "python3 db.py" to initialize your local copy of the sqlite db.

# Local development
To do local development, you should edit exampleenvvars.sh to reflect your local dev environment paths as well as the BeyondTrust ITOAPI token and then source the file before you execute runlocal.sh. You can find an example of envvars.sh with the relevant info in BeyondTrust in the "envvars for local dev" folder called auto-mate-envvars.sh.

# Explanation

This is a flask project that will take json files (stored in the json directory) and translate them into human-friendly (friendlier than AWX at least) forms that people can use to execute jobs via some type of portal. It also allows for other links such as to SOSAPI for convenience sake.

Users log in via their AD credentials, the app checks their AD groups, it compares the AD groups to the required AD groups in the json files, stores that in a database, and sends a randomly-generated session token that will expire after 10 minutes of inactivity. The token and cookie are renewed when the user navigates around the website.
