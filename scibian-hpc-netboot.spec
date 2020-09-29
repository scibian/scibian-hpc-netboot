%{!?__unit_dir:%global __unit_dir /etc/systemd/system}
%{!?__lib_dir:%global __lib_dir /usr/lib}
%define debug_package %{nil}

Name:	scibian-hpc-netboot
Version:	1.0
Release:	1%{?dist}.edf
License:	GPLv2+
Summary:	Suite of utilities for booting Scibian HPC clusters
URL:		https://github.com/scibian/scibian-hpc-netboot
Source0:	%{name}-%{version}.tar.gz
BuildRoot:	%(mktemp -ud %{_tmppath}/%{name}-%{version}-%{release}-XXXXXX)

%description
On Scibian HPC Clusters, when a node boot it needs some generated
configuration. This suite contains Python tools to generate these
configuration files through a CGI service.

%prep
%setup -q

%build

%install
install -m 755 -d %{buildroot}/etc/%{name}
install -m 755 -d %{buildroot}/etc/%{name}/menu
install -m 755 -d %{buildroot}/etc/%{name}/menu/entries.d
install -m 644 conf/boot-params.yaml %{buildroot}/etc/%{name}
install -m 644 conf/menu/*.jinja2 %{buildroot}/etc/%{name}/menu
install -m 644 conf/menu/entries.d/* %{buildroot}/etc/%{name}/menu/entries.d
install -m 755 -d %{buildroot}/etc/%{name}/installer
install -m 644 conf/installer/*.yaml %{buildroot}/etc/%{name}/installer
install -m 644 conf/installer/*.jinja2 %{buildroot}/etc/%{name}/installer
install -m 755 -d %{buildroot}/etc/%{name}/installer/schemas
install -m 755 -d %{buildroot}/etc/%{name}/installer/schemas/roles
install -m 755 -d %{buildroot}/etc/%{name}/installer/schemas/nodes
install -m 755 -d %{buildroot}/etc/%{name}/installer/schemas/common
install -m 755 -d %{buildroot}/usr/share/%{name}
install -m 644 lib/*.py %{buildroot}/usr/share/%{name}
install -m 755 -d %{buildroot}/var/www/cgi-bin/%{name}
install -m 755 scripts/*.py %{buildroot}/var/www/cgi-bin/%{name}

%clean
rm -rf %{buildroot}

%package common
Summary: %{name}-common Common files for netbooting Scibian HPC clusters nodes
Requires: python3, python3-pyyaml, python3-jinja2, python3-clustershell, httpd

%description common
This package provides a Python CGI script to generate dynamic iPXE bootmenu
based on a nodename in parameter and menu entries in a YAML file.

%files common
%defattr(-,root,root,-)
%dir /etc/%{name}
/etc/%{name}/boot-params.yaml
/usr/share/%{name}


%package menu
Summary: %{name}-menu iPXE bootmenu generator for Scibian HPC clusters
Requires: %{name}-common

%description menu
This package provides a Python CGI script to generate dynamic iPXE bootmenu
based on a nodename in parameter and menu entries in a YAML file.

%files menu
%defattr(-,root,root,-)
/etc/%{name}/menu
%dir /var/www/cgi-bin/%{name}
/var/www/cgi-bin/%{name}/bootmenu.py


%package preseedator
Summary: %{name}-preseedator d-i preseed generator for Scibian HPC clusters
Requires: %{name}-common

%description preseedator
This package provides Python CGI scripts to generate a debian-intasller preseed
for Scibian HPC cluster nodes and a specialized partition schema, based on the
nodename provided in parameter and a cYAML configuration file.

%files preseedator
%defattr(-,root,root,-)
/etc/%{name}/installer
%dir /var/www/cgi-bin/%{name}
/var/www/cgi-bin/%{name}/preseedator.py
/var/www/cgi-bin/%{name}/partitioner.py


%changelog

* Tue Sep 29 2020 Thomas HAMEL <thomas-t.hamel@edf.fr> - 1.0
- Initial RPM release
