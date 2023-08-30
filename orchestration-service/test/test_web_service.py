"""Module tests web service"""
import requests
import pytest
import re
import json

@pytest.fixture(scope="module")
def setup_module():
    """setting some constants to avoid mis-spellings"""
    setup = {}
    setup['base_url']='http://127.0.0.1:4000'

    setup['plain_text_headers'] = {
        'Accept': 'text/plain; charset=utf-8',
        'Content-Type': 'text/plain; charset=utf-8',
    }

    setup['json_headers'] = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
    }

    setup['html_headers'] = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
    }
    return setup


def test_job_redirect(setup_module):
    """Equivalent results request a job using the redirect, and request with 'nextjob' param"""
    cntx = setup_module

    # request a job test that /job follows redirect to /job?nextjob
    # both /job and /job?nextjob should result in the same response
    follow_redir_response = requests.get(cntx['base_url'] + '/job', headers=cntx['plain_text_headers'])
    assert follow_redir_response.status_code == 200

    params = { 'nextjob': 1 }
    direct_response = requests.get(cntx['base_url'] + '/job',
        params=params,
        headers=cntx['plain_text_headers'])

    #print (f"headers {direct_response.headers} content {direct_response.content}")
    assert direct_response.status_code == 200
    assert follow_redir_response.content == direct_response.content

def test_get_nextjob(setup_module):
    """Validate the data returned differs by Content Type"""
    cntx = setup_module
    # test plain text
    params = { 'nextjob': 1 }
    response_plain = requests.get(cntx['base_url'] + '/job', params=params, headers=cntx['plain_text_headers'])

    assert response_plain.status_code == 200
    plain_text_match = re.search(r"job_id=[0-9]+, replay_slice_id=1, start_block_num=1, end_block_num=100, status=WAITING_4_WORKER, last_block_processed=0, start_time=\d+-\d+-\d+T\d+:\d+:\d+, end_time=None, actual_integrity_hash=None",
        response_plain.content.decode('utf-8'))
    assert plain_text_match

    # test json
    params = { 'nextjob': 1 }
    response_json = requests.get(cntx['base_url'] + '/job', params=params, headers=cntx['json_headers'])

    assert response_json.status_code == 200
    print (response_json.content.decode('utf-8'))
    json_match = re.search(r"\{\"job_id\": [0-9]+, \"replay_slice_id\": 1, \"start_block_num\": 1, \"end_block_num\": 100, \"status\": \"WAITING_4_WORKER\", \"last_block_processed\": 0, \"start_time\": \"\d+-\d+-\d+T\d+:\d+:\d+\", \"end_time\": null, \"actual_integrity_hash\": null\}",
        response_json.content.decode('utf-8'))
    assert json_match

def test_update_job(setup_module):
    """Get a job update the status and validate the change is in place"""
    cntx = setup_module
    # test plain text
    params = { 'nextjob': 1 }
    response_first = requests.get(cntx['base_url'] + '/job', params=params, headers=cntx['json_headers'])
    assert response_first.status_code == 200

    # we are going to change status
    # validate status before change
    job_first_request = json.loads(response_first.content.decode('utf-8'))
    assert job_first_request['status'] != 'STARTED'

    # update status to STARTED
    params = { 'jobid': job_first_request['job_id'] }
    job_first_request['status'] = 'STARTED'

    # serialized dict to JSON when passing in
    updated_first = requests.post(cntx['base_url'] + '/job',
        params=params,
        headers=cntx['json_headers'],
        data=json.dumps(job_first_request))
    assert updated_first.status_code == 200

    # fetch again to validate update
    # validate status after change
    params = { 'jobid': job_first_request['job_id'] }
    validate_job_request = requests.get(cntx['base_url'] + '/job', params=params, headers=cntx['json_headers'])
    validate_job = json.loads(validate_job_request.content.decode('utf-8'))
    assert validate_job['status'] == 'STARTED'

    # restore job to enable reruns of tests
    validate_job['status'] = 'WAITING_4_WORKER'
    jobparams = { 'jobid': validate_job['job_id'] }
    updated = requests.post(cntx['base_url'] + '/job',
        params=jobparams,
        headers=cntx['json_headers'],
        data=json.dumps(validate_job))
        # this should always update
    assert updated.status_code == 200

def test_no_more_jobs(setup_module):
    """Using nextjob loop over the jobs updating status; eventually no more jobs and None is returned"""
    cntx = setup_module
    params = { 'nextjob': 1 }

    _ok = True
    counter = 0
    restore_jobs = []

    while _ok:
        nextjobparams = { 'nextjob': 1 }
        response = requests.get(cntx['base_url'] + '/job', params=nextjobparams, headers=cntx['json_headers'])
        # end on not found 404
        if response.status_code == 404:
            _ok = False
        # track how many good results
        if response.status_code == 200:
            counter += 1
        result = response.content
        # no infinite loops
        if counter > 10:
            break
        # update status to remove job from 'nextjob' queue
        if _ok:
            job = json.loads(result.decode('utf-8'))
            # save for later
            restore_jobs.append(job)
            # update status
            job['status'] = 'STARTED'
            jobparams = { 'jobid': job['job_id'] }
            updated = requests.post(cntx['base_url'] + '/job',
                params=jobparams,
                headers=cntx['json_headers'],
                data=json.dumps(job))
            # this should always update
            assert updated.status_code == 200
    # count differs depending on order of test execution
    assert counter > 1

    # restore job status otherwise reruns cause test failure
    for job in restore_jobs:
        # pass by reference not deep copy reset status
        job['status'] = 'WAITING_4_WORKER'
        jobparams = { 'jobid': job['job_id'] }
        updated = requests.post(cntx['base_url'] + '/job',
            params=jobparams,
            headers=cntx['json_headers'],
            data=json.dumps(job))
        # this should always update
        assert updated.status_code == 200

def test_status_reports(setup_module):
    """Request full status and check results"""
    cntx = setup_module

    response = requests.get(cntx['base_url'] + '/status', headers=cntx['json_headers'])
    assert response.status_code == 200
    assert len(response.content) > 500
    response = requests.get(cntx['base_url'] + '/status', headers=cntx['plain_text_headers'])
    assert response.status_code == 200
    assert len(response.content) > 500
    response = requests.get(cntx['base_url'] + '/status', headers=cntx['html_headers'])
    assert response.status_code == 200
    assert len(response.content) > 500
    # check position arg
    params = { 'pos': 1 }
    response = requests.get(cntx['base_url'] + '/status',
        params=params,
        headers=cntx['json_headers'])
    assert response.status_code == 200
    assert len(response.content) > 50
    response = requests.get(cntx['base_url'] + '/status',
        params=params,
        headers=cntx['plain_text_headers'])
    assert response.status_code == 200
    assert len(response.content) > 50
    response = requests.get(cntx['base_url'] + '/status',
        params=params,
        headers=cntx['html_headers'])
    assert response.status_code == 200
    assert len(response.content) > 50
