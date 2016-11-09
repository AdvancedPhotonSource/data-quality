#!/usr/bin/env python
# -*- coding: utf-8 -*-

# #########################################################################
# Copyright (c) 2016, UChicago Argonne, LLC. All rights reserved.         #
#                                                                         #
# Copyright 2016. UChicago Argonne, LLC. This software was produced       #
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

This module feeds the data coming from detector to a process using queue. It interracts with a channel access
plug in of area detector. The read of frame data from channel access happens on event of frame counter change.
The change is detected with a callback. The data is passed to the consuming process.
This module requires configuration file with the following parameters:
'detector', a string defining the first prefix in area detector, it has to match the area detector configuration
'detector_basic', a string defining the second prefix in area detector, defining the basic parameters, it has to
match the area detector configuration
'detector_image', a string defining the second prefix in area detector, defining the image parameters, it has to
match the area detector configuration
'no_frames', number of frames that will be fed
'args', optional, list of process specific parameters, they need to be parsed to the desired format in the wrapper
"""

from multiprocessing import Queue
import json
import sys
import dquality.common.utilities as utils
import dquality.common.report as report
from dquality.realtime.feed import feed_data



def init(config):
    """
    This function initializes global variables. It gets values from the configuration file, evaluates and processes
    the values. If mandatory parameter is missing, the script logs an error and exits.

    Parameters
    ----------
    config : str
        configuration file name, including path

    Returns
    -------
    logger : Logger
        logger instance

    limits : dictionary
        a dictionary containing limit values read from the configured 'limit' file

    quality_checks : dict
        a dictionary containing quality check functions ids
    """

    conf = utils.get_config(config)

    logger = utils.get_logger(__name__, conf)

    limitsfile = utils.get_file(conf, 'limits', logger)
    if limitsfile is None:
        sys.exit(-1)

    with open(limitsfile) as limits_file:
        limits = json.loads(limits_file.read())

    qcfile = utils.get_file(conf, 'quality_checks', logger)
    if qcfile is None:
        sys.exit(-1)

    with open(qcfile) as qc_file:
        dict = json.loads(qc_file.read())
    quality_checks = utils.get_quality_checks(dict)

    return logger, limits, quality_checks



def verify(conf, type = 'data', report_file=None, report_type = 'REPORT_FULL'):
    """
    HDF file structure verifier.

    Parameters
    ----------
    conf : str
        configuration file name, including path

    type : str
        a string characterizung the data type (i.e. data_dark, data_white or data)

    report_file : file
        a file where the report will be written, or None, if written to a console

    report_type : int
        report type, currently supporting REPORT_NONE, REPORT_ERRORS, and REPORT_FULL

    Returns
    -------
    boolean

    """

    logger, limits, quality_checks = init(conf)

    aggregateq = Queue()
    args = limits[type], aggregateq, quality_checks
    feed_data(conf, logger, *args)

    bad_indexes = {}
    aggregate = aggregateq.get()

    if report_file is not None:
        report.report_results(logger, aggregate, type, None, report_file, report_type)
    report.add_bad_indexes(aggregate, type, bad_indexes)

    return bad_indexes


