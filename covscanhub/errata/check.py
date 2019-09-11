# -*- coding: utf-8 -*-
"""
Functions related to checking provided data
"""

from __future__ import absolute_import
import os
import re
import logging
from django.core.exceptions import ObjectDoesNotExist
from kobo.django.upload.models import FileUpload

from covscanhub.errata.utils import depend_on
from covscanhub.other.exceptions import PackageBlacklistedException, PackageNotEligibleException
from covscanhub.scan.models import PackageAttribute, ScanBinding, ClientAnalyzer, Profile
from covscanhub.scan.xmlrpc_helper import cancel_scan

import koji
from kobo.rpmlib import parse_nvr
from django.conf import settings


logger = logging.getLogger(__name__)


def check_nvr(nvr):
    try:
        return parse_nvr(nvr)
    except ValueError:
        logger.error('%s is not a correct N-V-R', nvr)
        raise RuntimeError('%s is not a correct N-V-R' % nvr)


def check_package_eligibility(package, nvr, mock_profile, release, created):
    """
    check if package is eligible for scanning (it is not blacklisted)
    """
    if created:
        logger.info('Package %s for %s was created', package, release)
        # all freshly scanned packages are now eligible by default
        atr = PackageAttribute.create_eligible(package, release, True)
        is_eligible = atr.is_eligible()
    else:
        is_blocked = package.is_blocked(release)
        if is_blocked:
            raise PackageBlacklistedException('Package %s is blacklisted.' %
                                              (package.name))
        is_eligible = package.is_eligible(release)
    if not is_eligible:
        raise PackageNotEligibleException(
            'Package %s is not eligible for scanning.' % (package.name))


def check_package_is_blocked(package, release):
    is_blocked = package.is_blocked(release)
    if is_blocked:
        raise PackageBlacklistedException('Package %s is blacklisted.' %
                                          (package.name))


def check_obsolete_scan(package, release):
    bindings = ScanBinding.targets.by_package(package).by_release(release)
    for binding in bindings:
        if binding.scan.is_in_progress():
            cancel_scan(binding)


def check_build(nvr, check_additional=False):
    url = settings.BREW_URL
    bin = settings.BREW_BIN_NAME

    brew_proxy = koji.ClientSession(url)
    build = brew_proxy.getBuild(nvr)

    if not build and check_additional:
        url = settings.KOJI_URL
        bin = settings.KOJI_BIN_NAME
        brew_proxy = koji.ClientSession(url)
        build = brew_proxy.getBuild(nvr)
    if not build:
        raise RuntimeError("Brew build '%s' does not exist" % nvr)

    return nvr, url, bin


def check_analyzers(analyzers_chain, additional_analyzers=None):
    if analyzers_chain:
        a_list = ClientAnalyzer.chain_to_list(analyzers_chain)
    else:
        a_list = []
    if additional_analyzers:
        a_list += additional_analyzers
    logger.debug("Analyzers specified by client: %s", a_list)
    return ClientAnalyzer.objects.verify_in_bulk(a_list)


def check_upload(upload_id, task_user, is_tarball=False):
    """
    srpm was uploaded via FileUpload, lets fetch it and check it

    return (nvr, filename, path to srpm)
    """
    try:
        upload = FileUpload.objects.get(id=upload_id)
    except:
        raise ObjectDoesNotExist("Can't find uploaded file with id: %s" % upload_id)

    if upload.owner.username != task_user:
        raise RuntimeError("Can't process a file uploaded by a different user")

    srpm_path = os.path.join(upload.target_dir, upload.name)
    srpm_name = upload.name
    nvr = ''
    if not is_tarball:
        nvr = srpm_name.replace('.src.rpm', '')
    return nvr, srpm_name, srpm_path


def check_srpm(upload_id, build_nvr, task_user, is_tarball=False):
    if build_nvr:
        cb_response = check_build(build_nvr, check_additional=True)
        response = {
            'type': 'build',
            'nvr': cb_response[0],
            'koji_bin': cb_response[2],
            'koji_url': cb_response[1],
        }
    elif upload_id:
        cu_response = check_upload(upload_id, task_user, is_tarball)
        response = {
            'type': 'upload',
            'nvr': cu_response[0],
            'srpm_name': cu_response[1],
            'srpm_path': cu_response[2],
        }
    else:
        raise RuntimeError('No source RPM specified.')
    return response
