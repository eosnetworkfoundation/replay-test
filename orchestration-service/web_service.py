"""modules needed for web application"""
import json
from werkzeug.wrappers import Request, Response
from werkzeug.serving import run_simple
from replay_configuration import ReplayConfigManager
from job_status import JobManager

jobs = JobManager(ReplayConfigManager('../../meta-data/test-simple-jobs.json'))

@Request.application
# pylint: disable=too-many-return-statements disable=too-many-branches
def application(request):
    """using werkzeug and python create a web application that supports the following.
    A GET or POST request with the path '/job'.
    The '/job' GET request it can take a URL parameter of 'nextjob'
    with no value or a URL parameter of 'jobid' with an value.
    When 'nextjob' parameter is present the web application calls
    jobs.get_next_job() and returns the results in the body with a HTTP 200 code.
    When the 'jobid' parameter is present the web application will
    call jobs.get_job(jobid) and returns the results in the body with an HTTP 200 code.
    When no parameters are provided the web applications issues
    a 301 redirect to '/job?nextjob'
    If the content-type of the GET request is 'text/plain; charset=us-ascii'
    the results are formated as text string.
    If the content-type of the GET request is 'application/json'
    the results are formated as json.

    The '/job' POST request must have a URL parameter for 'job' with a value.
    If no parameter is present a 404 error is returned.
    The content-type of the POST request is always 'application/json'.
    The body of the POST request contains JSON which is parsed into a
    dictionary named updated_values and passed to the method 'job.set_job(updated_values)'

    Extend the application to include a request path '/status'
    '/status' GET and POST requests take one parameter 'jobid'
    For the GET request when parameter 'jobid' is present call 'jobs.get_job(jobid)'
    and return the status for that job. If the if content-type is text-html returns html
    if content-type is application/json returns json
    if content-type is text/plain return a string
    For the GET request when there are no parameters
    call 'jobs.get_all()' and return statuses for all jobs.
    If content-type is text-html returns html
    if content-type is application/json returns json
    if content-type is text/plain return a string

    The POST request '/status' must have a jobid parameter and value.
    For the POST request parse the json in the body as a
    dictionary and pass the dictionary to 'jobs.set_job(data)'
    When the POST request has no URL parameters return 404
    """
    if request.path == '/job':
        if request.method == 'GET':
            nextjob = request.args.get('nextjob')
            jobid = request.args.get('jobid')

            if nextjob is not None:
                result = jobs.get_next_job()
            elif jobid is not None:
                result = jobs.get_job(jobid)
            else:
                return Response("", status=301, headers={"Location": "/job?nextjob"})

            if request.headers.get('Content-Type') == 'text/plain; charset=us-ascii':
                return Response(str(result), content_type='text/plain; charset=us-ascii')
            if request.headers.get('Content-Type') == 'application/json':
                return Response(json.dumps(result), content_type='application/json')

        elif request.method == 'POST':
            job = request.args.get('job')
            if not job:
                return Response("Job parameter is missing", status=404)

            data = request.get_json()
            if not data:
                return Response("Invalid JSON data", status=400)

            jobs.set_job(data)
            return Response(json.dumps({"status": "updated"}), content_type='application/json')

    elif request.path == '/status':
        jobid = request.args.get('jobid')
        content_type = request.headers.get('Content-Type')

        if request.method == 'GET':
            if jobid:
                result = jobs.get_job(jobid)
            else:
                result = jobs.get_all()

            if content_type == 'text/html':
                # Converting to simple HTML representation (adjust as needed)
                return Response("<br>".join([f"{k}: {v}" \
                    for item in result for k, v in item.items()]),
                    content_type='text/html')
            if content_type == 'application/json':
                return Response(json.dumps(result),
                content_type='application/json')
            if content_type == 'text/plain':
                return Response("\n".join([f"{k}: {v}" \
                for item in result for k, v in item.items()]),
                content_type='text/plain')

        elif request.method == 'POST':
            if not jobid:
                return Response("JobID parameter is missing", status=404)

            data = request.get_json()
            if not data:
                return Response("Invalid JSON data", status=400)

            jobs.set_job(data)
            return Response(json.dumps({"status": "updated"}), content_type='application/json')

    return Response("Not found", status=404)

if __name__ == '__main__':
    run_simple('127.0.0.1', 4000, application)



# POST with jobid parses body and updates  status for that job
# POST with no jobid return 404 error
# /restart POST with bearer token
# POST parses body to get bearer_token. If bearer_token matches sets all jobs to status "terminated"
# /healthcheck
# GET request always returns 200 OK
