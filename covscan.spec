Name:           covscan
Version:        0.8.0
Release:        3%{?dist}
License:        Commercial
Summary:        Coverity scan scheduler
Source:         %{name}-%{version}.tar.bz2
BuildArch:      noarch

BuildRequires:  python3-devel
BuildRequires:  python3-six
BuildRequires:  python3-kobo-client

%{?!git_version: %global git_version %{version}}

%description
CovScan is a Coverity scan scheduler.
It consists of central hub, workers and cli client.


%package client
Summary: CovScan CLI client
Requires: koji
Requires: python3-kobo-client >= 0.15.1-100
Requires: %{name}-common = %{git_version}-%{release}
Obsoletes: python3-%{name}-client < %{git_version}-%{release}

%description client
CovScan CLI client


%package common
Summary: CovScan shared files for client, hub and worker

%description common
CovScan shared files for client, hub and worker.


%package worker
Summary: CovScan worker
Requires: csmock
Requires: koji
Requires: python3-kobo-client
Requires: python3-kobo-rpmlib
Requires: python3-kobo-worker
Requires: %{name}-common = %{git_version}-%{release}
Requires: %{name}-worker-conf = %{git_version}-%{release}
Obsoletes: covscan-worker-prod < %{git_version}-%{release}
Obsoletes: covscan-worker-stage < %{git_version}-%{release}
Obsoletes: python3-%{name}-worker < %{git_version}-%{release}
Obsoletes: python3-covscan-worker-prod < %{git_version}-%{release}
Obsoletes: python3-covscan-worker-stage < %{git_version}-%{release}

%description worker
CovScan worker

%package hub
Summary: CovScan xml-rpc interface and web application
Requires: boost-python3
Requires: httpd
Requires: mod_auth_gssapi
Requires: python3-django
Requires: python3-kobo-client
Requires: python3-kobo-django
Requires: python3-kobo-hub
Requires: python3-kobo-rpmlib
Requires: python3-mod_wsgi
# PostgreSQL adapter for python
Requires: python3-psycopg2
Requires: gzip
# inform ET about progress using UMB (Unified Message Bus)
Requires: python3-qpid-proton
# hub is interacting with brew
Requires: koji
# extract tarballs created by csmock
Requires: xz

Requires: csdiff
Requires: file
Requires: python3-bugzilla
Requires: python3-csdiff

Requires: python3-django-debug-toolbar > 1.0

Requires: %{name}-common = %{git_version}-%{release}
Requires: %{name}-hub-conf = %{git_version}-%{release}
Obsoletes: covscan-hub-prod < %{git_version}-%{release}
Obsoletes: covscan-hub-stage < %{git_version}-%{release}
Obsoletes: python3-covscan-hub-prod < %{git_version}-%{release}
Obsoletes: python3-covscan-hub-stage < %{git_version}-%{release}
Obsoletes: python3-%{name}-hub < %{git_version}-%{release}

%description hub
CovScan xml-rpc interface and web application

# define covscan-{worker,hub}-conf-{devel,stage,prod} subpackages
%(for sub in worker hub; do
for alt in devel stage prod; do
cat << EOF
%package ${sub}-conf-${alt}
Summary: Covscan ${sub} ${alt} configuration
Provides: covscan-${sub}-conf = %{git_version}-%{release}
Conflicts: covscan-${sub}-conf
RemovePathPostfixes: .${alt}
%description ${sub}-conf-${alt}
Covscan ${sub} ${alt} configuration
EOF
done;done)

%prep
%setup -q

%build
%py3_build


%install
rm -rf ${RPM_BUILD_ROOT}
%py3_install

# avoid transforming /usr/bin/env -S ... to /usr/bin/-S
%global __brp_mangle_shebangs_exclude_from %{_bindir}/covscan

# tweak python paths in config files

# FIXME
sed -i 's@/lib/python2.[0-9]@/lib/python%{python3_version}@g' ${RPM_BUILD_ROOT}/etc/httpd/conf.d/covscanhub-httpd.conf.*

# create /var/lib dirs
mkdir -p $RPM_BUILD_ROOT/var/lib/covscanhub/tasks
mkdir -p $RPM_BUILD_ROOT/var/lib/covscanhub/upload

# create log file
mkdir -p $RPM_BUILD_ROOT/var/log/covscanhub
touch $RPM_BUILD_ROOT/var/log/covscanhub/covscanhub.log

# copy checker_groups.txt
cp -R covscanhub/scripts/checker_groups.txt $RPM_BUILD_ROOT/%{python3_sitelib}/covscanhub/scripts/

# make manage.py executable
chmod 0755 $RPM_BUILD_ROOT%{python3_sitelib}/covscanhub/manage.py

%files client
%defattr(644,root,root,755)
%attr(755,root,root) /usr/bin/covscan
%attr(644,root,root) %config(noreplace) /etc/covscan/covscan.conf
%{_sysconfdir}/bash_completion.d/
%{python3_sitelib}/covscan
%{python3_sitelib}/covscan-%{version}-py%{python3_version}.egg-info

%files common
%defattr(644,root,root,755)
%{python3_sitelib}/covscancommon

%files worker
%defattr(644,root,root,755)
%{python3_sitelib}/covscand
%attr(755,root,root) /etc/init.d/covscand
%attr(754,root,root) /usr/sbin/covscand

%files worker-conf-devel
%attr(640,root,root) %config(noreplace) /etc/covscan/covscand.conf

%files worker-conf-stage
%attr(640,root,root) %config(noreplace) /etc/covscan/covscand.conf.stage

%files worker-conf-prod
%attr(640,root,root) %config(noreplace) /etc/covscan/covscand.conf.prod

%files hub
%defattr(-,root,apache,-)
%{python3_sitelib}/covscanhub
%exclude %{python3_sitelib}/covscanhub/settings_local.py*
%dir %attr(775,root,apache) /var/log/covscanhub
%ghost %attr(640,apache,apache) /var/log/covscanhub/covscanhub.log
%dir %attr(775,root,apache) /var/lib/covscanhub
%dir %attr(775,root,apache) /var/lib/covscanhub/tasks
%dir %attr(775,root,apache) /var/lib/covscanhub/upload

%files hub-conf-devel
%{python3_sitelib}/covscanhub/settings_local.py

%files hub-conf-stage
%{python3_sitelib}/covscanhub/settings_local.py.stage
%attr(640,root,root) %config(noreplace) /etc/httpd/conf.d/covscanhub-httpd.conf.stage

%files hub-conf-prod
%{python3_sitelib}/covscanhub/settings_local.py.prod
%attr(640,root,root) %config(noreplace) /etc/httpd/conf.d/covscanhub-httpd.conf.prod


%changelog
* Thu Apr 07 2022 Lumír Balhar <lbalhar@redhat.com> - 0.8.0-3
- Reorganize specfile and add covscan-common

* Mon Mar 14 2022 Kamil Dudka <kdudka@redhat.com> - 0.8.0-2
- add obsoletes to ease upgrade

* Thu Jan 20 2022 Kamil Dudka <kdudka@redhat.com> - 0.8.0-1
- drop support for python 2.x and django 1.x
- new major release

* Thu Nov 04 2021 Kamil Dudka <kdudka@redhat.com> - 0.7.2-1
- new release

* Thu Mar 25 2021 Kamil Dudka <kdudka@redhat.com> - 0.7.1-1
- new release

* Tue Dec 22 2020 Kamil Dudka <kdudka@redhat.com> - 0.7.0-1
- new release

* Thu Oct 24 2019 Matej Mužila <mmuzila@redhat.com> - 0.6.12-3
- spec changes to build python3 covscan

* Thu Sep 19 2019 Kamil Dudka <kdudka@redhat.com> - 0.6.12-2
- explicitly require python2-* build dependencies

* Tue Sep 03 2019 Kamil Dudka <kdudka@redhat.com> - 0.6.12-1
- new release

* Fri Oct 19 2018 Kamil Dudka <kdudka@redhat.com> - 0.6.11-1
- new release

* Mon Aug 13 2018 Kamil Dudka <kdudka@redhat.com> - 0.6.10-1
- new release

* Fri Oct 20 2017 Kamil Dudka <kdudka@redhat.com> - 0.6.9-1
- new release

* Mon Jun 26 2017 Kamil Dudka <kdudka@redhat.com> - 0.6.8-1
- new release

* Tue Apr 12 2016 Kamil Dudka <kdudka@redhat.com> - 0.6.7-2
- bump release to force update if stale covscan-testing packages are installed

* Thu Aug 20 2015 Kamil Dudka <kdudka@redhat.com> - 0.6.7-1
- 0.6.7 bugfix release

* Wed Aug 12 2015 Kamil Dudka <kdudka@redhat.com> - 0.6.6-1
- 0.6.6 bugfix release
- update the list of dependencies
- create empty /var/log/covscanhub.log unless it exists already

* Thu Feb 19 2015 Tomas Tomecek <ttomecek@redhat.com> - 0.6.5-1
- 0.6.5 bugfix release

* Wed Dec 10 2014 Tomas Tomecek <ttomecek@redhat.com> - 0.6.4-1
- update CLI docs (--help) and homepage
- workaround a race on server when running multiple tasks

* Tue Nov 04 2014 Tomas Tomecek <ttomecek@redhat.com> - 0.6.3-1
- enable passing args to csmock from client
- fix several TBs

* Mon Oct 20 2014 Tomas Tomecek <ttomecek@redhat.com> - 0.6.2-1
- enable submitting prio from cli
- pass cmock args to version task

* Mon Oct 13 2014 Tomas Tomecek <ttomecek@redhat.com> - 0.6.1-1
- bugfix update: fix version-diff-build

* Sat Oct 11 2014 Tomas Tomecek <ttomecek@redhat.com> - 0.6.0-1
- 0.6.0 release
- add profiles

* Thu Sep 25 2014 Tomas Tomecek <ttomecek@redhat.com> - 0.6.0-1.a
- 0.6.0a alpha release

* Mon Aug 04 2014 Tomas Tomecek <ttomecek@redhat.com> - 0.5.2-1
- add DB fixtures to package

* Mon Aug 04 2014 Tomas Tomecek <ttomecek@redhat.com> - 0.5.1-1
- fixes for reworked scheduler

* Wed Jan 8 2014 Tomas Tomecek <ttomecek@redhat.com> - 0.4.4-1
- remove brewkoji dependency

* Sun Nov 17 2013 Tomas Tomecek <ttomecek@redhat.com> - 0.4.3-1
- hub update (django and kobo rebase)

* Fri Oct 18 2013 Tomas Tomecek <ttomecek@redhat.com> - 0.4.2-2
- update kobo dependency (0.4.1 should be fine)
- add scriptlets for handling issues with kobo-0.4.0

* Mon Sep 30 2013 Tomas Tomecek <ttomecek@redhat.com> - 0.4.1-2
- make dependency to kobo 0.3.8 (0.4 is broken currently)

* Fri Sep 13 2013 Tomas Tomecek <ttomecek@redhat.com> - 0.4.1-1
- improve stats
- bugfixes

* Wed Sep 11 2013 Tomas Tomecek <ttomecek@redhat.com> - 0.4.0-1
- new version of hub and client

* Mon Jun 03 2013 Tomas Tomecek <ttomecek@redhat.com> - 0.3.2-3
- store provider requests in DB (hub)

* Thu May 23 2013 Tomas Tomecek <ttomecek@redhat.com> - 0.3.2-2
- New release of hub, bugfixes and RFEs
- Getting ready for 6.5 scanning

* Thu May 23 2013 Tomas Tomecek <ttomecek@redhat.com> - 0.3.2-1
- Update to version 0.3.2

* Wed Apr 24 2013 Tomas Tomecek <ttomecek@redhat.com> - 0.3.1-1
- Update to version 0.3.1

* Fri Apr 5 2013 Tomas Tomecek <ttomecek@redhat.com> - 0.3.0-1
- Update for hub and worker
- ET pilot

* Fri Mar 15 2013 Tomas Tomecek <ttomecek@redhat.com> - 0.2.3-1
- Let client depend on brewkoji
- new version

* Thu Jan 24 2013 Tomas Tomecek <ttomecek@redhat.com> - 0.2.2-2
- Tarball extraction fix

* Wed Jan 09 2013 Tomas Tomecek <ttomecek@redhat.com> - 0.2.2-1
- Added support for multiple new options (CLI)

* Tue Nov 06 2012 Tomas Tomecek <ttomecek@redhat.com> - 0.2.1-2
- Updated requirements for hub and worker

* Thu Nov 1 2012 Tomas Tomecek <ttomecek@redhat.com> - 0.2.1-1
- Added version-diff-build (CLI, HUB, worker)
- Improved WebUI (scans, waiver) (HUB)
- Implemented functionality for ET scans (HUB, worker)
- Fixed several bugs on worker (worker)
- Tarball on hub is now automatically extracted (worker, HUB)
- You may browse more types of log files (.out, .html, etc.) (HUB)

* Thu Dec  8 2011 Daniel Mach <dmach@redhat.com> - 0.2.0-1
- Implement a mock-build command and brew build support. (Daniel Mach)
- Minor tweaks to hub settings and client configuration. (Daniel Mach)
- Add a --timeout option to the diff-build command. (Daniel Mach)

* Tue Jun 14 2011 Daniel Mach <dmach@redhat.com> - 0.1.0-1
- Initial build.
