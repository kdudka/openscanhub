# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright contributors to the OpenScanHub project.

import os
import re
import sys
from urllib.request import urlretrieve
from xmlrpc.client import Fault

import koji


def check_analyzers(proxy, analyzers_list):
    result = proxy.scan.check_analyzers(analyzers_list)
    if isinstance(result, str):
        raise RuntimeError(result)


def verify_build_exists(build, profile):
    """
    Verify if build exists
    """
    try:
        cfg = koji.read_config(profile)
    except koji.ConfigurationError as e:
        print('koji:', e, file=sys.stderr)
        return False

    proxy_object = koji.ClientSession(cfg['server'])
    try:
        # getBuild XML-RPC call is defined here: ./hub/kojihub.py:3206
        returned_build = proxy_object.getBuild(build)
    except koji.GenericError:
        return False

    return returned_build is not None and \
        returned_build.get('state', None) == koji.BUILD_STATES['COMPLETE']


def verify_koji_build(build, profiles):
    """
    Verify if brew or koji build exists
    """
    srpm = os.path.basename(build)  # strip path if any
    if srpm.endswith(".src.rpm"):
        srpm = srpm[:-8]

    # Get dist tag
    match = re.search('.*-.*-(.*)', srpm)
    if not match:
        return f'Invalid N-V-R: {srpm}'
    dist_tag = match[1]

    # Parse Koji profiles
    koji_profiles = profiles.split(',')
    if '' in koji_profiles:
        return f'Koji profiles could not be parsed properly: {koji_profiles}'

    # Use brew first unless fc is in the dist tag.
    # In that case, start with Fedora Koji.
    if 'fc' in dist_tag and 'brew' == koji_profiles[0]:
        koji_profiles.reverse()

    if any(verify_build_exists(build, p) for p in koji_profiles):
        return None

    return f"Build {build} does not exist in {koji_profiles}, has its files \
deleted, or did not finish successfully."


def verify_mock(mock, hub):
    mock_conf = hub.mock_config.get(mock)
    if not mock_conf:
        return f"Mock config {mock} does not exist."
    if not mock_conf["enabled"]:
        return f"Mock config {mock} is not enabled."
    return None


def handle_perm_denied(e, parser):
    """DRY"""
    if 'PermissionDenied: Login required.' in e.faultString:
        parser.error('You are not authenticated. Please \
obtain Kerberos ticket or specify username and password.')
    raise


def fetch_results(dest, task_url, nvr):
    """Downloads results for the given task URL"""
    # we need nvr + '.tar.xz'
    if nvr.endswith('.src.rpm'):
        tarball = os.path.basename(nvr).replace('.src.rpm', '.tar.xz')
    else:
        tarball = nvr + '.tar.xz'

    # get absolute path
    dest_dir = os.path.abspath(dest if dest is not None else os.curdir)
    local_path = os.path.join(dest_dir, tarball)

    # task_url is url to task with trailing '/'
    url = f"{task_url}log/{tarball}?format=raw"

    print(f"Downloading {tarball}", file=sys.stderr)
    urlretrieve(url, local_path)


def upload_file(hub, srpm, target_dir, parser):
    """Upload file to hub, catch PermDenied exception"""
    try:
        # returns (upload_id, err_code, err_msg)
        return hub.upload_file(os.path.expanduser(srpm), target_dir)
    except Fault as e:
        handle_perm_denied(e, parser)
