"""modules needed for web application"""
import argparse
import json
import sys
from werkzeug.wrappers import Request, Response
from werkzeug.serving import run_simple
from werkzeug.http import generate_etag
from report_templates import ReportTemplate
from replay_configuration import ReplayConfigManager
from job_status import JobManager

def create_summary():
    """Creates data object for summary report"""
    total_blocks = 0
    blocks_processed = 0
    total_jobs = 0
    jobs_succeeded = 0
    jobs_failed = 0
    failed_jobs = []
    for this_job in jobs.get_all().items():
        # caculate progress
        total_blocks += this_job.slice_config.end_block_id - this_job.slice_config.start_block_id
        if this_job.last_block_processed > 0:
            blocks_processed += this_job.last_block_processed - this_job.slice_config.start_block_id

        # calculate jobs
        total_jobs += 1
        if this_job.status.name == "COMPLETE":
            if this_job.slice_config.expected_integrity_hash == this_job.actual_integrity_hash:
                jobs_succeeded += 1
            else:
                jobs_failed += 1
                failed_jobs.append(
                    {
                    'status': 'COMPLETE',
                    'jobid': this_job.job_id ,
                    'configid': this_job.slice_config.replay_slice_id
                    })
        if this_job.status.name == "ERROR" or this_job.status.name == "TIMEOUT":
                jobs_failed += 1
                failed_jobs.append(
                    {
                    'status': 'COMPLETE',
                    'jobid': this_job.job_id ,
                    'configid': this_job.slice_config.replay_slice_id
                    })
        return {
            'total_blocks': total_blocks,
            'blocks_processed': blocks_processed,
            'total_jobs': total_jobs,
            'jobs_succeeded': jobs_succeeded,
            'jobs_failed': jobs_failed,
            'failed_jobs': failed_jobs
        }

@Request.application
# pylint: disable=too-many-return-statements disable=too-many-branches
# pylint: disable=too-many-statements
def application(request):
    """
    using werkzeug and python create a web application that supports
    /job
    /status
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
    Content Type {request.headers.get('Content-Type')}
    Accept  {request.headers.get('Accept')}
    ETag {request.headers.get('ETag')}""")
    if request.path == '/job':
        # capture Accept Header
        request_accept_type = request.headers.get('Accept')

        # Work through GET Requests first
        if request.method == 'GET':

            # Handle URL Parameters
            if request.args.get('jobid') is not None:
                result = jobs.get_job(request.args.get('jobid'))
            elif 'nextjob' in request.args.keys():
                result = jobs.get_next_job()
            else:
                return Response("", status=301, headers={"Location": "/job?nextjob"})

            # Check we have a legit value
            if result is None:
                return Response("Could not find job", status=404)

            etag_value = generate_etag(str(result.as_dict()).encode("utf-8"))

            # Format based on content type
            # content type is None when no content-type passed in
            # redirect strips content type
            # DEFAULT and PLAIN TEXT
            if ('text/plain; charset=utf-8' in request_accept_type or
                'text/plain' in request_accept_type or
                '*/*' in request_accept_type or
                request_accept_type is None):
                response = Response(str(result), content_type='text/plain; charset=utf-8')
                response.headers['ETag'] = etag_value
                return response
            # JSON
            if 'application/json' in request_accept_type:
                response = Response(json.dumps(result.as_dict()), content_type='application/json')
                response.headers['ETag'] = etag_value
                return response

        # Work through POST Requests
        elif request.method == 'POST':
            request_etag = request.headers.get('ETag')

            # must have jobid parameter
            if not request.args.get('jobid'):
                return Response('jobid parameter is missing', status=404)
            # validate etags to avoid race conditions
            job_as_str = str(
                jobs.get_job(request.args.get('jobid')).as_dict()
                ).encode("utf-8")
            expected_etag = generate_etag(job_as_str)
            if expected_etag != request_etag:
                return Response("Invalid ETag", status=400)

            data = request.get_json()
            if not data:
                return Response("Invalid JSON data", status=400)

            # expects id to exist
            if not 'job_id' in data:
                data['job_id'] = request.args.get('jobid')
            # check bool success for set_job to ensure valid data
            if jobs.set_job(data):
                stringified = str(
                    jobs.get_job(request.args.get('jobid')).as_dict()
                    ).encode("utf-8")
                etag_value = generate_etag(stringified)
                response = Response(
                    json.dumps({"status": "updated"}),
                    content_type='application/json')
                response.headers['ETag'] = etag_value
                return response
            return Response("Invalid job JSON data", status=400)

    elif request.path == '/status':
        # Capture the Accept Type
        request_accept_type = request.headers.get('Accept')
        replay_slice = request.args.get('sliceid')
        results = []

        # Handle URL Parameters
        if request.method == 'GET':
            # if id push one element into an array
            # else return the entire array
            if replay_slice:
                this_slice = jobs.get_by_position(replay_slice)

                # check if not set and results empty
                if this_slice is None:
                    return Response("Not found", status=404)
                # set the slice
                results.append(this_slice)

            else:
                for this_slice in jobs.get_all().items():
                    results.append(this_slice[1])

            # Format based on content type
            # content type is None when no content-type passed in
            # redirect strips content type
            # HTML
            if 'text/html' in request_accept_type:
                # Converting to simple HTML representation (adjust as needed)
                content = ReportTemplate.status_html_report(results)
                return Response(content, content_type='text/html')
            # JSON
            if 'application/json' in request_accept_type:
                # Converting from object to dictionarys to dump json
                results_as_dict = [obj.as_dict() for obj in results]
                return Response(json.dumps(results_as_dict),content_type='application/json')
            # DEFAULT and PLAIN TEXT
            if ('text/plain; charset=utf-8' in request_accept_type or
                'text/plain' in request_accept_type or
                '*/*' in request_accept_type or
                request_accept_type is None):
                # Converting to simple Text format
                content = ReportTemplate.status_html_report(results)
                return Response(content,content_type='text/plain; charset=uft-8')

    elif request.path == '/config':
        # Capture the Accept Type
        request_accept_type = request.headers.get('Accept')
        slice_id = request.args.get('sliceid')
        this_config = replay_config_manager.get(slice_id)

        # only GET with param
        if request.method == 'GET' and slice_id is not None:
            # Format based on content type
            # content type is None when no content-type passed in
            # redirect strips content type
            # HTML
            if 'text/html' in request_accept_type:
                # Converting to simple HTML representation (adjust as needed)
                content = ReportTemplate.config_html_report(this_config)
                return Response(content, content_type='text/html')
            # JSON
            if ('application/json' in request_accept_type or
                '*/*' in request_accept_type or
                request_accept_type is None):
                # Converting from object to dictionarys to dump json
                results_as_dict = this_config.as_dict()
                return Response(json.dumps(results_as_dict),content_type='application/json')

        elif request.method == 'POST':
            # posted json body end_block_id and integrity_hash
            # return sliceid and message
            data = request.get_json()
            if not data:
                return Response("Invalid JSON data", status=400)

            block = replay_config_manager.return_record_by_end_block_id(int(data['end_block_num']))
            block.expected_integrity_hash = data['integrity_hash']
            replay_config_manager.set(block)
            replay_config_manager.persist()

            response_message = {
                'sliceid': block.replay_slice_id,
                'message': 'updated integrity hash'
            }

            return Response(json.dumps(response_message),content_type='application/json')

    elif request.path == '/healthcheck':
        return Response("OK",content_type='text/plain; charset=uft-8')

    elif request.path == '/':
        content = ReportTemplate.home_html_report()
        return Response(content, content_type='text/html')

    elif request.path == '/summary':
        request_accept_type = request.headers.get('Accept')
        report_obj = create_summary()
        # Format based on content type
        # content type is None when no content-type passed in
        # HTML
        if 'text/html' in request_accept_type:
            # Converting to simple HTML representation (adjust as needed)
            content = ReportTemplate.summary_html_report(report_obj)
            return Response(content, content_type='text/html')
        # JSON
        if 'application/json' in request_accept_type:
            return Response(json.dumps(report_obj),content_type='application/json')
        # DEFAULT and PLAIN TEXT
        if ('text/plain; charset=utf-8' in request_accept_type or
            'text/plain' in request_accept_type or
            '*/*' in request_accept_type or
            request_accept_type is None):
            # Converting to simple Text format
            content = ReportTemplate.summary_text_report(report_obj)
            return Response(content,content_type='text/plain; charset=uft-8')

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
