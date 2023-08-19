# /job GET
# takes one param jobid and returns json for job
# returns 404 error when no parameters are supplied
# /status GET and POST
# takes one param jobid
# GET with jobid returns status for that job
# GET with no params reports status for all jobs
# if content-type is text-html returns html
# if content-type is application/json returns json
# if content-type is text/plain
# POST with jobid parses body and updates  status for that job
# POST with no jobid return 404 error
# /restart POST with bearer token
# POST parses body to get bearer_token. If bearer_token matches sets all jobs to status "terminated"
# /healthcheck
# GET request always returns 200 OK
