#!/usr/bin/env python
# -*- coding: utf-8 -*-

# #########################################################################
# Copyright (c) 2015, UChicago Argonne, LLC. All rights reserved.         #
#                                                                         #
# Copyright 2015. UChicago Argonne, LLC. This software was produced       #
# under U.S. Government contract DE-AC02-06CH11357 for Argonne National   #
# Laboratory (ANL), which is operated by UChicago Argonne, LLC for the    #
# U.S. Department of Energy. The U.S. Government has rights to use,       #
# reproduce, and distribute this software.  NEITHER THE GOVERNMENT NOR    #
# UChicago Argonne, LLC MAKES ANY WARRANTY, EXPRESS OR IMPLIED, OR        #
# ASSUMES ANY LIABILITY FOR THE USE OF THIS SOFTWARE.  If software is     #
# modified to produce derivative works, such modified software should     #
# be clearly marked, so as not to confuse it with the version available   #
# from ANL.                                                               #
#                                                                         #
# Additionally, redistribution and use in source and binary forms, with   #
# or without modification, are permitted provided that the following      #
# conditions are met:                                                     #
#                                                                         #
#     * Redistributions of source code must retain the above copyright    #
#       notice, this list of conditions and the following disclaimer.     #
#                                                                         #
#     * Redistributions in binary form must reproduce the above copyright #
#       notice, this list of conditions and the following disclaimer in   #
#       the documentation and/or other materials provided with the        #
#       distribution.                                                     #
#                                                                         #
#     * Neither the name of UChicago Argonne, LLC, Argonne National       #
#       Laboratory, ANL, the U.S. Government, nor the names of its        #
#       contributors may be used to endorse or promote products derived   #
#       from this software without specific prior written permission.     #
#                                                                         #
# THIS SOFTWARE IS PROVIDED BY UChicago Argonne, LLC AND CONTRIBUTORS     #
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT       #
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS       #
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL UChicago     #
# Argonne, LLC OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,        #
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,    #
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;        #
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER        #
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT      #
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN       #
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE         #
# POSSIBILITY OF SUCH DAMAGE.                                             #
# #########################################################################
"""
Please make sure the installation :ref:`pre-requisite-reference-label` are met.

This script is specific for beamline 32id.

This example takes one mandatory parameter, and three optional:
instrument: a string defining the detector that will be used. User can enter one of these choices: 
'nanotomo', 'microtomo'. The instrument determines a configuration file that will be used.
type: data type to be verified (i.e. data_dark, data_white or data), defaulted to 'data'
report_file: name of report file, defaulted to None
report_type: report type, currently supporting REPORT_NONE, REPORT_ERRORS, and REPORT_FULL, defaulted to REPORT_FULL.

This script calls real_time verifier.

"""
import sys
import os
import argparse
from dquality.realtime.check import realtime as rt
from os.path import expanduser

def main(arg):
    parser = argparse.ArgumentParser()
    parser.add_argument("instrument", help="instrument name, name should have a matching directory in the .dquality folder")
    parser.add_argument("--type", default="data", help="optional, data type to be verified (i.e. data_dark, data_white or data)")
    parser.add_argument("--report_file", default=None, help="optional, name of report file")
    parser.add_argument("--report_type", default="REPORT_FULL", help="optional, report type, currently supporting REPORT_NONE, REPORT_ERRORS, and REPORT_FULL")

    args = parser.parse_args()
    instrument = args.instrument
    type = args.type
    report_file = args.report_file
    report_type = args.report_type

    home = expanduser("~")
    conf = os.path.join(home, ".dquality", instrument)

    bad_indexes = rt(conf, type, report_file, report_type)
    return bad_indexes


if __name__ == "__main__":
    main(sys.argv[1:])


