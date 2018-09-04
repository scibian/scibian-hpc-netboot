#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2018 Scibian Project <legal@scibian.org>
#
# This file is part of scibian-hpc-netboot.
#
# scibian-hpc-netboot is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# scibian-hpc-netboot is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU General Public License
# along with scibian-hpc-netboot.  If not, see <http://www.gnu.org/licenses/>.

import ClusterShell.NodeSet
import yaml
import logging
import logging.handlers
import cgi
import sys
import os
import re
from jinja2 import Template, Environment, FileSystemLoader


""" Library file with all classes and functions for Scibian HPC netboot CGI
    scripts. """

class MenuEntry(object):


    def __init__(self, app, os, media, version):

        self.app = app  # ref to NetbootAppMenu (for logger and
                        # node_boot_params)
        self.os = os
        self.media = media
        self.version = version
        self.label = None
        self.dir = None
        self.initrd = None
        self.kernel = None
        self.opts = None

    def fill(self, entry_fields):
        """Render entry_fields (which can be templated) with parameters from
           BootParams and self MenuEntry context."""
        self.label = self.render_entry_field(entry_fields['label'])
        if entry_fields.has_key('dir'):
            self.dir = self.render_entry_field(entry_fields['dir'])
            if not self.dir.endswith('/'):
                self.dir += '/'
        else:
            self.dir = ''
        self.initrd = self.render_entry_field(entry_fields['initrd'])
        self.kernel = self.render_entry_field(entry_fields['kernel'])
        self.opts = self.render_entry_field(entry_fields['opts'])

    def render_entry_field(self, value):
        context = self.app.node_boot_params.dump
        context.update({ 'os':      self.os,
                         'media':   self.media,
                         'version': self.version,
                         'initrd':  self.initrd })
        return Template(value).render(context)

    @property
    def name(self):

        return '-'.join([self.os, self.media, self.version])

    def __repr__(self):

        return self.name

    @property
    def base_url(self):
       if self.media == 'disk':
           return "http://"+ self.app.node_boot_params['diskinstall_server'] + "/disk/" + self.os
       elif self.media == 'ram':
           return "http://" + self.app.node_boot_params['diskless_server'] + "/" + self.os
       else:
           self.app.logger.error('unknown media %s', self.media)
           return 'fail'

    @property
    def initrd_url(self):
       return "${base-url}/"+ self.dir + self.initrd

    @property
    def kernel_url(self):
       return "${base-url}/"+ self.dir + self.kernel


class NodeBootParams(object):


    def __init__(self, node):

        self.content = None
        self.node = node

    def __getitem__(self, key):
        """Lookup a specific boot params."""
        # search for node specific value
        for nodeset in self.content:
            if nodeset != 'defaults' and \
               self.node in ClusterShell.NodeSet.expand(nodeset) and \
               key in self.content[nodeset]:
                return self.content[nodeset][key]
        # return defaults value
        return self.content['defaults'][key]

    @property
    def dump(self):
        """Return all current node boot parameters in a dict."""
        xparams = self.content['defaults'].copy()
        # search for node specific value
        for nodeset in self.content:
            if nodeset != 'defaults' and \
               self.node in ClusterShell.NodeSet.expand(nodeset):
                 # override all nodes specific params
                 for key, value in self.content[nodeset].iteritems():
                     xparams[key] = value
        return xparams

    def __repr__(self):

        return repr(self.dump)

    def load(self):
        self.content = yaml.load(open('/etc/scibian-hpc-netboot/boot-params.yaml'))


class NetbootAppGeneric(object):

    """Generic application class, parent of all specialized applications
       classes."""

    def __init__(self, name, node, debug):

        self.name = name
        self.node = node
        self.node_boot_params = NodeBootParams(node)

        # setup logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        s_handler = logging.handlers.SysLogHandler(address = '/dev/log')
        s_formatter = logging.Formatter('%(name)s: %(message)s')
        s_handler.setFormatter(s_formatter)
        s_handler.setLevel(logging.INFO)
        self.logger.addHandler(s_handler)

        if debug is True:
            f_handler = logging.StreamHandler()
            f_formatter = logging.Formatter('%(name)s: %(levelname)s: %(message)s')
            f_handler.setFormatter(f_formatter)
            f_handler.setLevel(logging.DEBUG)
            self.logger.addHandler(f_handler)

    def read_conf(self):

        self.node_boot_params.load()

    def render_generic(self, dirname, template, context):
        dirpath = os.path.join('/etc/scibian-hpc-netboot/', dirname)
        self.logger.debug("node: %s dir: %s template: %s context: %s",
                          self.node, dirpath, template, repr(context))
        jenv = Environment(loader=FileSystemLoader(dirpath),
                       trim_blocks=True)
        print jenv.get_template(template).render(context)


class NetbootAppMenu(NetbootAppGeneric):

    def __init__(self, node, debug):

        super(NetbootAppMenu, self).__init__('scibian-hpc-bootmenu', node, debug)
        self.entries = []

    @property
    def default_entry(self):
        return MenuEntry(self,
                         self.node_boot_params['os'],
                         self.node_boot_params['media'],
                         self.node_boot_params['version']).name

    def read_conf(self):
        super(NetbootAppMenu, self).read_conf()

        y_entries = yaml.load(open('/etc/scibian-hpc-netboot/menu/entries.yaml'))

        for os, medias in y_entries.iteritems():
            for media, versions in medias.iteritems():
                for version, entry_fields in versions.iteritems():
                    entry = MenuEntry(self, os, media, version)
                    entry.fill(entry_fields)
                    self.entries.append(entry)

    def render(self):

        default = self.default_entry
        self.logger.info("generating menu for " + self.node + " with default entry: " + default)
        context = { 'entries': self.entries,
                    'node': self.node,
                    'default_entry': default }
        self.render_generic('menu', 'ipxe.menu.jinja2', context)


class NetbootAppPreseed(NetbootAppGeneric):

    def __init__(self, node, debug):

        super(NetbootAppPreseed, self).__init__('scibian-hpc-preseedator', node, debug)
        self.installer = None

    def read_conf(self):

        super(NetbootAppPreseed, self).read_conf()
        self.installer = yaml.load(open('/etc/scibian-hpc-netboot/installer/installer.yaml'))

    def render(self):

        self.logger.info("generating preseed for " + self.node)
        context = { 'node': self.node_boot_params }
        context.update(self.installer)
        self.render_generic('installer', 'preseed.jinja2', context)


class NetbootAppPartitioner(NetbootAppGeneric):


    def __init__(self, node, debug):

        super(NetbootAppPartitioner, self).__init__('scibian-hpc-partitioner', node, debug)

    def read_conf(self):

        super(NetbootAppPartitioner, self).read_conf()

    @property
    def role(self):
        """Compute node role based on node name and cluster prefix. """
        noderole_re_s = r"%s([a-z0-9]*[a-z]+)\d+" % (self.node_boot_params['prefix'])
        match = re.search(noderole_re_s, self.node)
        if match is None:
            self.logger.error('unable to extract role name from nodename %s',
                         self.none)
            sys.exit(1)
        return match.group(1)


    def render(self):
        """This render() method does not relies on a template, it just returns
           the most specialized partition schema existing for the node, in this
           order:
             1/ for the node
             2/ for the role
             3/ common
        """
        base_path = '/etc/scibian-hpc-netboot/installer/schemas'
        for xpath in [ 'nodes/%s' % (self.node),
                       'roles/%s' % (self.role),
                       'common' ]:
            schema_path = os.path.join(base_path, xpath)
            if os.path.exists(schema_path):
                self.logger.info("return schema %s for node %s",
                                 schema_path, self.node)
                print('Content-Type: text/plain\n')
                with open(schema_path, 'r') as f_schema:
                    print f_schema.read()
                break
            else:
                self.logger.debug("schema %s does not exist", schema_path)


def run_app(app_class):

    """Generic Utility to instanciate the spcialized application."""

    params = cgi.FieldStorage()
    debug = False
    if 'debug' in params:
        debug = True
    app = app_class(params.getvalue('node'), debug)

    # Comment the lines above and uncomment the following line to run the CGI
    # scripts on CLI for testing purposes.
    #app = app_class(sys.argv[1], debug=True)

    app.read_conf()
    app.render()
