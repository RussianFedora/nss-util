%global nspr_version 4.8.9

Summary:          Network Security Services Utilities Library
Name:             nss-util
Version:          3.13.1
Release:          3%{?dist}.R
License:          MPLv1.1 or GPLv2+ or LGPLv2+
URL:              http://www.mozilla.org/projects/security/pki/nss/
Group:            System Environment/Libraries
Requires:         nspr >= %{nspr_version}
BuildRoot:        %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
BuildRequires:    nspr-devel >= %{nspr_version}
BuildRequires:    zlib-devel
BuildRequires:    pkgconfig
BuildRequires:    gawk
BuildRequires:    psmisc
BuildRequires:    perl

Source0:          %{name}-%{version}.tar.bz2
# The nss-util tar ball is a subset of nss-{version}-stripped.tar.bz2, 
# Therefore we use the nss-split-util.sh script to keeping only what we need.
# Download the nss tarball via CVS from the nss propect and follow these
# steps to make the r tarball for nss-util out of the for nss:
# fedpkg clone nss
# fedpkg clone nss-util
# cd nss-util/master
# cp ../../nss/devel/${version}-stripped.tar.bz2 .
# sh ./nss-split-util.sh ${version}
# A file named {name}-{version}.tar.bz2 should appear
Source1:          nss-split-util.sh
Source2:          nss-util.pc.in
Source3:          nss-util-config.in

# remove when we update pick up the fix from upstream
Patch24:           gnuc-minor-def-fix.patch

%description
Utilities for Network Security Services and the Softoken module

# We shouln't need to have a devel subpackage as util will be used in the
# context of nss or nss-softoken. keeping to please rpmlint.
# 
%package devel
Summary:          Development libraries for Network Security Services Utilities
Group:            Development/Libraries
Requires:         nss-util = %{version}-%{release}
Requires:         nspr-devel >= %{nspr_version}
Requires:         pkgconfig

%description devel
Header and library files for doing development with Network Security Services.


%prep
%setup -q
# remove when we update and pick up the fix from upstream
%patch24 -p1 -b .gnuc-minor

%build

# Enable compiler optimizations and disable debugging code
BUILD_OPT=1
export BUILD_OPT

# Uncomment to disable optimizations
#RPM_OPT_FLAGS=`echo $RPM_OPT_FLAGS | sed -e 's/-O2/-O0/g'`
#export RPM_OPT_FLAGS

# Generate symbolic info for debuggers
XCFLAGS=$RPM_OPT_FLAGS
export XCFLAGS

PKG_CONFIG_ALLOW_SYSTEM_LIBS=1
PKG_CONFIG_ALLOW_SYSTEM_CFLAGS=1

export PKG_CONFIG_ALLOW_SYSTEM_LIBS
export PKG_CONFIG_ALLOW_SYSTEM_CFLAGS

NSPR_INCLUDE_DIR=`/usr/bin/pkg-config --cflags-only-I nspr | sed 's/-I//'`
NSPR_LIB_DIR=`/usr/bin/pkg-config --libs-only-L nspr | sed 's/-L//'`

export NSPR_INCLUDE_DIR
export NSPR_LIB_DIR

NSS_USE_SYSTEM_SQLITE=1
export NSS_USE_SYSTEM_SQLITE

%ifarch x86_64 ppc64 ia64 s390x sparc64
USE_64=1
export USE_64
%endif

# make util
%{__make} -C ./mozilla/security/coreconf
%{__make} -C ./mozilla/security/nss

# Set up our package file
%{__mkdir_p} ./mozilla/dist/pkgconfig
%{__cat} %{SOURCE2} | sed -e "s,%%libdir%%,%{_libdir},g" \
                          -e "s,%%prefix%%,%{_prefix},g" \
                          -e "s,%%exec_prefix%%,%{_prefix},g" \
                          -e "s,%%includedir%%,%{_includedir}/nss3,g" \
                          -e "s,%%NSPR_VERSION%%,%{nspr_version},g" \
                          -e "s,%%NSSUTIL_VERSION%%,%{version},g" > \
                          ./mozilla/dist/pkgconfig/nss-util.pc

NSSUTIL_VMAJOR=`cat mozilla/security/nss/lib/util/nssutil.h | grep "#define.*NSSUTIL_VMAJOR" | awk '{print $3}'`
NSSUTIL_VMINOR=`cat mozilla/security/nss/lib/util/nssutil.h | grep "#define.*NSSUTIL_VMINOR" | awk '{print $3}'`
NSSUTIL_VPATCH=`cat mozilla/security/nss/lib/util/nssutil.h | grep "#define.*NSSUTIL_VPATCH" | awk '{print $3}'`

export NSSUTIL_VMAJOR 
export NSSUTIL_VMINOR 
export NSSUTIL_VPATCH

%{__cat} %{SOURCE3} | sed -e "s,@libdir@,%{_libdir},g" \
                          -e "s,@prefix@,%{_prefix},g" \
                          -e "s,@exec_prefix@,%{_prefix},g" \
                          -e "s,@includedir@,%{_includedir}/nss3,g" \
                          -e "s,@MOD_MAJOR_VERSION@,$NSSUTIL_VMAJOR,g" \
                          -e "s,@MOD_MINOR_VERSION@,$NSSUTIL_VMINOR,g" \
                          -e "s,@MOD_PATCH_VERSION@,$NSSUTIL_VPATCH,g" \
                          > ./mozilla/dist/pkgconfig/nss-util-config

chmod 755 ./mozilla/dist/pkgconfig/nss-util-config


%install

%{__rm} -rf $RPM_BUILD_ROOT

# There is no make install target so we'll do it ourselves.

%{__mkdir_p} $RPM_BUILD_ROOT/%{_includedir}/nss3
%{__mkdir_p} $RPM_BUILD_ROOT/%{_libdir}
%{__mkdir_p} $RPM_BUILD_ROOT/%{_libdir}/nss3
%{__mkdir_p} $RPM_BUILD_ROOT/%{_libdir}/pkgconfig
%{__mkdir_p} $RPM_BUILD_ROOT/%{_bindir}

for file in libnssutil3.so
do
  %{__install} -p -m 755 mozilla/dist/*.OBJ/lib/$file $RPM_BUILD_ROOT/%{_libdir}
done

# Copy the include files we want
# The util headers, the rest come from softokn and nss
for file in mozilla/dist/public/nss/*.h
do
  %{__install} -p -m 644 $file $RPM_BUILD_ROOT/%{_includedir}/nss3
done

# Copy the package configuration files
%{__install} -p -m 644 ./mozilla/dist/pkgconfig/nss-util.pc $RPM_BUILD_ROOT/%{_libdir}/pkgconfig/nss-util.pc
%{__install} -p -m 755 ./mozilla/dist/pkgconfig/nss-util-config $RPM_BUILD_ROOT/%{_bindir}/nss-util-config

%clean
%{__rm} -rf $RPM_BUILD_ROOT

%post -p /sbin/ldconfig

%postun -p /sbin/ldconfig

%files
%defattr(-,root,root)
%{_libdir}/libnssutil3.so

%files devel
%defattr(-,root,root)
# package configuration files
%{_libdir}/pkgconfig/nss-util.pc
%{_bindir}/nss-util-config

# co-owned with nss
%dir %{_includedir}/nss3
# these are marked as public export in
# mozilla/security/nss/lib/util/manifest.mk
%{_includedir}/nss3/base64.h
%{_includedir}/nss3/ciferfam.h
%{_includedir}/nss3/nssb64.h
%{_includedir}/nss3/nssb64t.h
%{_includedir}/nss3/nsslocks.h
%{_includedir}/nss3/nssilock.h
%{_includedir}/nss3/nssilckt.h
%{_includedir}/nss3/nssrwlk.h
%{_includedir}/nss3/nssrwlkt.h
%{_includedir}/nss3/nssutil.h
%{_includedir}/nss3/pkcs11.h
%{_includedir}/nss3/pkcs11f.h
%{_includedir}/nss3/pkcs11n.h
%{_includedir}/nss3/pkcs11p.h
%{_includedir}/nss3/pkcs11t.h
%{_includedir}/nss3/pkcs11u.h
%{_includedir}/nss3/portreg.h
%{_includedir}/nss3/secasn1.h
%{_includedir}/nss3/secasn1t.h
%{_includedir}/nss3/seccomon.h
%{_includedir}/nss3/secder.h
%{_includedir}/nss3/secdert.h
%{_includedir}/nss3/secdig.h
%{_includedir}/nss3/secdigt.h
%{_includedir}/nss3/secerr.h
%{_includedir}/nss3/secitem.h
%{_includedir}/nss3/secoid.h
%{_includedir}/nss3/secoidt.h
%{_includedir}/nss3/secport.h
%{_includedir}/nss3/utilrename.h

%changelog
* Thu Jan 26 2012 Arkady L. Shane <ashejn@russianfedora.ru> - 3.13.1-3.R
- rebuilt for EL

* Fri Dec 02 2011 Elio Maldonado Batiz <emaldona@redhat.com> - 3.13.1-3
- Retagging

* Fri Dec 02 2011 Elio Maldonado <emaldona@redhat.com> - 3.13.1-2
- Fix a gnuc def typo

* Thu Nov 03 2011 Elio Maldonado <emaldona@redhat.com> - 3.13.1-1
- Update to NSS_3_13_1_RTM

* Sat Oct 15 2011 Elio Maldonado <emaldona@redhat.com> - 3.13-1
- Update to NSS_3_13_RTM

* Thu Oct 07 2011 Elio Maldonado <emaldona@redhat.com> - 3.13-0.1.rc0.1
- Update to NSS_3_13_RC0

* Thu Sep  8 2011 Ville Skyttä <ville.skytta@iki.fi> - 3.12.11-2
- Avoid %%post/un shell invocations and dependencies.

* Tue Aug 09 2011 Elio Maldonado <emaldona@redhat.com> - 3.12.11-1
- Update to NSS_3_12_11_RTM

* Fri May 06 2011 Elio Maldonado <emaldona@redhat.com> - 3.12.10-1
- Update to NSS_3_12_10_RTM

* Mon Apr 25 2011 Elio Maldonado Batiz <emaldona@redhat.com> - 3.12.10-0.1.beta1
- Update to NSS_3_12_10_BETA1

* Tue Feb 08 2011 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 3.12.9-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_15_Mass_Rebuild

* Wed Jan 12 2011 Elio Maldonado <emaldona@redhat.com> - 3.12.9-1
- Update to 3.12.9

* Mon Dec 27 2010 Elio Maldonado <emaldona@redhat.com> - 3.12.9-0.1beta2
- Rebuilt according to fedora pre-release package naming guidelines

* Fri Dec 10 2010 Elio Maldonado <emaldona@redhat.com> - 3.12.8.99.2-1
- Update to NSS_3_12_9_BETA2

* Wed Dec 08 2010 Elio Maldonado <emaldona@redhat.com> - 3.12.8.99.1-1
- Update to NSS_3_12_9_BETA1

* Wed Sep 29 2010 jkeating - 3.12.8-2
- Rebuilt for gcc bug 634757

* Thu Sep 23 2010 Elio Maldonado <emaldona@redhat.com> - 3.12.8-1
- Update to 3.12.8

* Sat Sep 18 2010 Elio Maldonado <emaldona@redhat.com> - 3.12.7.99.4-1
- NSS 3.12.8 RC0

* Sat Sep 04 2010 Elio Maldonado <emaldona@redhat.com> - 3.12.7.99.3-1
- NSS 3.12.8 Beta 3

* Sat Aug 29 2010 Elio Maldonado <emaldona@redhat.com> - 3.12.7-2
- Define NSS_USE_SYSTEM_SQLITE and remove nolocalsql patch 

* Mon Aug 16 2010 Elio Maldonado <emaldona@redhat.com> - 3.12.7-1
- Update to 3.12.7

* Fri Mar 05 2010 Elio Maldonado <emaldona@redhat.com> - 3.12.6-1
- Update to 3.12.6

* Mon Jan 18 2010 Elio Maldonado <emaldona@redhat.com> - 3.12.5-2
- Fix in nss-util-config.in

* Thu Dec 03 2009 Elio Maldonado<emaldona@redhat.com> - 3.12.5-1
- Update to 3.12.5

* Thu Sep 10 2009 Elio Maldonado<emaldona@redhat.com> - 3.12.4-8
- Retagging for a chained build with nss-softokn and nss

* Thu Sep 10 2009 Elio Maldonado<emaldona@redhat.com> - 3.12.4-5
- Restoring -rpath-link to nss-util-config

* Tue Sep 08 2009 Elio Maldonado<emaldona@redhat.com> - 3.12.4-4
- Installing shared libraries to %%{_libdir}

* Sat Sep 05 2009 Elio Maldonado<emaldona@redhat.com> - 3.12.4-3
- Remove symbolic links to shared libraries from devel - 521155
- Apply nss-nolocalsql patch subset for nss-util
- No rpath-link in nss-util-config

* Fri Sep 04 2009 Elio Maldonado<emaldona@redhat.com> - 3.12.4-2
- Retagging for a chained build

* Thu Sep 03 2009 Elio Maldonado<emaldona@redhat.com> - 3.12.4-1
- Update to 3.12.4
- Don't require sqlite

* Thu Aug 27 2009 Elio Maldonado<emaldona@redhat.com> - 3.12.3.99.3-15
- Bump the release number for a chained build of nss-util, nss-softokn and nss

* Thu Aug 27 2009 Elio Maldonado<emaldona@redhat.com> - 3.12.3.99.3-14
- Cleanup nss-util-config.in

* Thu Aug 27 2009 Elio Maldonado<emaldona@redhat.com> - 3.12.3.99.3-13
- nss-util-devel doesn't require nss-devel

* Wed Aug 26 2009 Elio Maldonado<emaldona@redhat.com> - 3.12.3.99.3-12
- bump to unique nvr

* Wed Aug 26 2009 Elio Maldonado<emaldona@redhat.com> - 3.12.3.99.3-11
- Remove spurious executable permissions from nss-util-config
- Shorten some descriptions to keep rpmlint happy

* Mon Aug 24 2009 Dennis Gilmore <dennis@ausil.us> 3.12.3.99.3-10
- dont include the headers in nss-util only in the -devel package
- nss-util-devel Requires nss-devel since its only providing a subset of the headers.

* Thu Aug 20 2009 Dennis Gilmore <dennis@ausil.us> 3.12.3.99.3-9
- Provide nss-devel since we obsolete it

* Thu Aug 19 2009 Elio Maldonado <emaldona@redhat.com> 3.12.3.99.3-8.1
- nss-util-devel obsoletes nss-devel < 3.12.3.99.3-8

* Thu Aug 19 2009 Elio Maldonado <emaldona@redhat.com> 3.12.3.99.3-8
- Initial build
