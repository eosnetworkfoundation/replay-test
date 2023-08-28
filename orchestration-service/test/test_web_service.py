"""Module tests web service"""
import requests
import pytest
import re

@pytest.fixture(scope="module")
def setup_module():
    setup = {}
    setup['base_url']='http://127.0.0.1:4000'

    setup['plain_text_headers'] = {
        'Content-Type': 'text/plain; charset=utf-8',
    }

    setup['json_headers'] = {
        'Content-Type': 'application/json',
    }
    return setup


def test_job_redirect(setup_module):
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

def test_get_job(setup_module):
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
