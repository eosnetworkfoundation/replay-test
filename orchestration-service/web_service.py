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
    """
    using werkzeug and python create a web application that supports
    /job
    /status
    /restart
    /healthcheck
    """
    # /job GET request
    # two params nextjob with no values or jobid with a value
    # when no params redirect to /job?nextjob
    #
    # nextjob get the next job ready for work, idle replay node would pick this up
    # jobid get the configuration for a job
    #
    # how the results are reported depends on content-type passed in
    # results could come page as text or json
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
                return Response(json.dumps(result.as_dict()), content_type='application/json')

        elif request.method == 'POST':
            jobid = request.args.get('jobid')
            if not jobid:
                return Response("jobid parameter is missing", status=404)

            data = request.get_json()
            if not data:
                return Response("Invalid JSON data", status=400)

            jobs.set_job_from_json(data, jobid)
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
# /reset POST with bearer token
# POST parses body to get bearer_token. If bearer_token matches sets all jobs to status "terminated"
# /healthcheck
# GET request always returns 200 OK
