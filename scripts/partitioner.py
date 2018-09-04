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

import cgi
import sys
sys.path.insert(0, '/usr/share/scibian-hpc-netboot')

from ScibianHPCNetboot import NetbootAppPartitioner, run_app

""" Scibian HPC partitioner: gives the most specialized partition schema
    for a given node. """

def main():

    run_app(NetbootAppPartitioner)


if __name__ == '__main__':
    main()
