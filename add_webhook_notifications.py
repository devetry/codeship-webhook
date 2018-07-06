"""
Add a webhook notification for all projects in a codeship organization
"""

import six
import sys
import time
import getpass
import requests as reqsts

class PatientRequester(object):
    """
    proxy to requests, but ensure that each request duration is
    at least 1 second to avoid blowing rate limits.
    """
    def __init__(self, duration=1):
        self.duration = duration
    
    def __getattr__(self, method):
        def patient_method(*args, **kwargs):
            start = time.time()
            resp = getattr(reqsts, method)(*args, **kwargs)
            end = time.time()
            req_dur = end - start
            if 0 < req_dur < self.duration:
                time.sleep(self.duration - req_dur)
            return resp
        return patient_method

requests = PatientRequester()

def login():
    """
    prompt for username, password, and hit the /auth endpoint
    to get an access_token
    """
    username = six.moves.input('username (email): ')
    password = getpass.getpass()
    resp = requests.post('https://api.codeship.com/v2/auth', auth=(username, password))
    resp.raise_for_status()
    data = resp.json()

    org = choose_org(data['organizations'])
    return org['uuid'], data['access_token']

def choose_org(orgs):
    writable_orgs = [o for o in orgs if 'project.write' in o['scopes']]
    if not writable_orgs:
        six.print_('Unable to find orgs where you have project.write permissions')
        for org in orgs:
            six.print_('', o['name'], 'scopes:', ','.join(o['scopes']))
        sys.exit(1)
    if len(writable_orgs) == 1:
        resp = six.moves.input("Set webhooks for all projects on '{}'? (Y/n)".format(writable_orgs[0]['name']))
        if 'n' in resp.lower():
            six.print_('no org chosen. exiting.')
            sys.exit(0)
        return writable_orgs[0]
    six.print_('Set webhooks for all projects on which org?')
    for ix, org in enumerate(orgs):
        six.print_('', ix, o['name'])
    ix = name = None
    resp = six.moves.input('(enter a name or number) ')
    try:
        ix = int(resp)
        return orgs[ix]
    except ValueError:
        name = resp
        for org in orgs:
            if org['name'].lower() == name.lower():
                return org
    six.print_("didn't recognize org '{}'. exiting.".format(resp))
    sys.exit(1)

def get_webhook_choice():
    url = six.moves.input('enter webhook url: ')
    return url.strip()

def project_page(org_id, access_token, page=0):
    resp = requests.get(
        'https://api.codeship.com/v2/organizations/{}/projects?per_page=50&page={}'.format(org_id, page),
        headers={
            'Authorization': 'Bearer ' + access_token,
        },
    )
    resp.raise_for_status()
    return resp.json()['projects']

def all_projects(org_id, access_token):
    page = 0
    while True:
        projects = project_page(org_id, access_token, page)
        if not projects:
            break
        for proj in projects:
            yield proj
        page += 1

def curl_string(request, exclude_auth=False):
    # construct the curl command from request
    url = request.url
    method = request.method
    headers = request.headers
    body = request.body
    command = "curl -X {method} {uri} {headers} {data}"
    data = ""
    if body:
        data = " -d '" + body + "'"

    excluded_headers = EXCLUDED_HEADERS + ('Authorization',) if exclude_auth else ()
    header_list = ["-H '{}: {}'".format(k, v) for k, v in headers.items()
                   if k not in excluded_headers]
    header = " ".join(header_list)
    return command.format(method=method, headers=header, data=data, uri=url)


def update_project(org_id, access_token, project, webhook):
    six.print_('  Updating project {}...'.format(project['name']), end=' ')
    six.moves.input('okay?')
    for notification in project['notification_rules']:
        if notification['notifier'] == 'webhook' and notification['options']['url'] == webhook:
            six.print_('done (already had webhook)')
            return
    
    project['notification_rules'].append({
        'branch': None,
        'branch_match': 'exact',
        'build_statuses': ['failed', 'started', 'recovered', 'success'],
        'notifier': 'webhook',
        'options': {
            'url': webhook,
        },
    })

    resp = requests.put(
        'https://api.codeship.com/v2/organizations/{}/projects/{}'.format(org_id, project['uuid']),
        headers={
            'Authorization': 'Bearer ' + access_token,
        },
        json=dict(
            type=project['type'],
            setup_commands=project['setup_commands'],
            team_ids=project['team_ids'],
            notification_rules=project['notification_rules'],
            environment_variables=project['environment_variables'],
        ),
    )
    six.print_('response', resp.text)
    six.print_('request as curl: ', curl_string(resp.request))
    resp.raise_for_status()
    six.print_('done')

if __name__ == '__main__':
    org_id, access_token = login()
    webhook = get_webhook_choice()
    for project in all_projects(org_id, access_token):
        update_project(org_id, access_token, project, webhook)