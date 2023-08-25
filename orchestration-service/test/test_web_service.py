"""Module tests web service"""
import requests
import pytest

@pytest.fixture(scope="module")
def setup_module():
    setup = {}
    setup['base_url']='http://127.0.0.1:4000'

    setup['plain_text_headers'] = {
        'Content-Type': 'text/plain; charset=uft-8',
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

    params = { 'nextjob': None }
    direct_response = requests.get(cntx['base_url'] + '/job', params=params, headers=cntx['plain_text_headers'])

    #print (f"headers {direct_response.headers} content {direct_response.content}")
    assert direct_response.status_code == 200
    assert follow_redir_response.content == direct_response.content
