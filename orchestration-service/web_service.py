"""modules needed for web application"""
import argparse
import json
import sys
from werkzeug.wrappers import Request, Response
from werkzeug.serving import run_simple
from report_templates import ReportTemplate
from replay_configuration import ReplayConfigManager
from job_status import JobManager

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
    print (f"""\nSTART: Request Path {request.path}
    Method {request.method}
    Params {request.args.keys()}
    Content Type {request.headers.get('Content-Type')}""")
    if request.path == '/job':
        # capture Content-Type
        request_content_type = request.headers.get('Content-Type')

        # Work through GET Requests first
        if request.method == 'GET':
            jobid = request.args.get('jobid')

            # Handle URL Parameters
            if jobid is not None:
                result = jobs.get_job(jobid)
            elif 'nextjob' in request.args.keys():
                result = jobs.get_next_job()
            else:
                return Response("", status=301, headers={"Location": "/job?nextjob"})

            # Format based on content type
            # content type is None when no content-type passed in
            # redirect strips content type
            # DEFAULT and PLAIN TEXT
            if (request_content_type == 'text/plain; charset=utf-8' or
                request_content_type == 'text/plain' or
                request_content_type is None):
                return Response(str(result), content_type='text/plain; charset=utf-8')
            # JSON
            if request_content_type == 'application/json':
                return Response(json.dumps(result.as_dict()), content_type='application/json')

        # Work through POST Requests
        elif request.method == 'POST':

            # must have jobid parameter
            jobid = request.args.get('jobid')
            if not jobid:
                return Response("jobid parameter is missing", status=404)

            data = request.get_json()
            if not data:
                return Response("Invalid JSON data", status=400)

            # no need to validate content type
            jobs.set_job_from_json(data, jobid)
            return Response(json.dumps({"status": "updated"}), content_type='application/json')

    elif request.path == '/status':
        # Capture the Content-Type
        request_content_type = request.headers.get('Content-Type')
        jobid = request.args.get('jobid')
        results = {}

        # Handle URL Parameters
        if request.method == 'GET':
            if jobid:
                results['job'] = jobs.get_job(jobid)
            else:
                results = jobs.get_all()

            # Format based on content type
            # content type is None when no content-type passed in
            # redirect strips content type
            # HTML
            if request_content_type == 'text/html':
                # Converting to simple HTML representation (adjust as needed)
                content = ReportTemplate.job_html_header()
                for job in results.values():
                    content += ReportTemplate.job_html(job)
                content += ReportTemplate.job_html_footer()
                return Response(content, content_type='text/html')
            # JSON
            if request_content_type == 'application/json':
                # Converting from object to dictionarys to dump json
                jobs_as_dict = {key: obj.as_dict() for key, obj in results.items()}
                return Response(json.dumps(jobs_as_dict),content_type='application/json')
            # DEFAULT and PLAIN TEXT
            if (request_content_type == 'text/plain; charset=utf-8' or
                request_content_type == "text/plain" or request_content_type is None):
                # Converting to simple Text format
                content = ReportTemplate.job_text_header()
                for job in results.values():
                    content += str(job)
                content += ReportTemplate.job_text_footer()
                return Response(content,content_type='text/plain; charset=uft-8')

        elif request.method == 'POST':
            if not jobid:
                return Response("JobId parameter is missing", status=404)

            data = request.get_json()
            if not data:
                return Response("Invalid JSON data", status=400)

            jobs.set_job(data)
            return Response(json.dumps({"status": "updated"}), content_type='application/json')

    return Response("Not found", status=404)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Orchestration Service \
to manage tests to replay on the antelope blockchain')
    parser.add_argument('--config', '-c', type=str, help='Path to config json')
    parser.add_argument('--port', type=int, default=4000, help='Port for web service')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='Listening service name or ip')

    args = parser.parse_args()

    # remove this if Local config works
    if args.config is None:
        sys.exit("Must provide config with --config option")
    replay_config_manager = ReplayConfigManager(args.config)
    jobs = JobManager(replay_config_manager)
    run_simple(args.host, args.port, application)

# POST with jobid parses body and updates  status for that job
# POST with no jobid return 404 error
# /reset POST with bearer token
# POST parses body to get bearer_token. If bearer_token matches sets all jobs to status "terminated"
# /healthcheck
# GET request always returns 200 OK
