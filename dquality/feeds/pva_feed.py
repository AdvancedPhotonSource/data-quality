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

This module feeds the data coming from detector to a process using queue.
"""

from multiprocessing import Queue
import numpy as np
import dquality.feeds.adapter as adapter
import dquality.common.constants as const


__author__ = "Barbara Frosik"
__copyright__ = "Copyright (c) 2016, UChicago Argonne, LLC."
__docformat__ = 'restructuredtext en'
__all__ = ['start_feed',
           'stop_feed'
           'on_change']


class Feed:
    """
    This class reads frames in a real time, and delivers to consuming process.
    """

    def __init__(self, pva_name):
        """
        Constructor
        """
        # for communication with pvaccess - receiving data
        self.chan = pvaccess.Channel(pva_name)
        x, y = self.chan.get('field()')['dimension']
        self.x = x['size']
        self.y = y['size']
        self.counter = -1

        # for communication with handler - delivering data
        self.dataq = Queue()


    def start_feed(self):
        self.chan.subscribe('update', self.on_change)
        self.chan.startMonitor("value,attribute,uniqueId")


    def stop_feed(self):
        data = adapter.pack_data(None, const.DATA_STATUS_END)
        self.dataq.put(data)
        self.chan.stopMonitor()
        self.chan.unsubscribe('update')


    def on_change(self, v):
        self.no_frames_left = self.no_frames_left - 1
        if self.no_frames_left == 0:
            self.stop_feed()
        else:
            if self.counter == -1:
                self.counter = v['uniqueId'] - 1  # self.counter keeps previous id
                img_data = v['value'][0]['ubyteValue']
                # compute black point and gain from first frame
                self.black, white = np.percentile(img_data, [0.01, 99.99])
                self.gain = 255 / (white - self.black)
                labels = [item["name"] for item in v["attribute"]]
                self.theta_key = labels.index("SampleRotary")

            #img_data = v['value'][0]['ubyteValue']
            img_data = v['value'][0]['ushortValue']
            img_data = (img_data - self.black) * self.gain
            img_data = np.clip(img_data, 0, 255).astype('uint8')

            # resize to get a 2D array from 1D data structure
            img_data = np.resize(img_data, (self.y, self.x))

            theta = v["attribute"][self.theta_key]["value"][0]["value"]

            counter = v['uniqueId']
            self.counter += 1
            while self.counter < counter:
                data = adapter.pack_data(None, const.DATA_STATUS_MISSING)
                self.dataq.put(data)
                self.counter += 1

            args = {}
            args["SampleRotary"] = theta
            data = adapter.pack_data(img_data, 'data', **args)
            self.dataq.put(data)


    def feed_data(self, no_frames, logger, *args):
        """
        This function is called by a client to start the process.
        """
        self.no_frames_left = no_frames
        adapter.start_process(self.dataq, logger, *args)
        self.start_feed()

