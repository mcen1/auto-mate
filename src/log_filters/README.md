These will replace lines in the job file based on either simple strings or a regex.

PLEASE NOTE that the HTML output that AWX provides is not very informational about what state the job is in. To that end, the portal checks the output and makes decisions based off the output. The most crucial thing is that the portal will assume the job is still launching if neither "TASK" or "PLAY" appear in the AWX job output. So, if you filter those out, then the portal will think the job is waiting to launch forever.
