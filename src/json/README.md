This is where you put the files that get translated into a form. NOTE: your AWX job needs the middleware_user to be allowed "execute" access on your job in order for this to work.

Minimum job params:
```
{
  "awx-job-name": "name-of-your-awx-job",
  "portal-endpoint": "web_friendly_url_endpoint_that_is_unique",
  "valid-ad-groups": ["CN=ADGroupName,DC=company,DC=com","someothergroup"],
  "job-type": "awx",
  "run-via": ["form"],
  "category": "ITOA",
  "friendly-name": "User-friendly Title for People to Click",
  "form-elements":[
    {"friendly-name":"Please supply something:","type":"text","max-length":32, "var-name":"yourextravarname", "required": true }
  ],
  "description": "Description of job that will appear at top of page."
}
```

See "allinputs" for examples of additional form-elements.
