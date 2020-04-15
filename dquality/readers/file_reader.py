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

This module verifies a configured hd5 file. The data is verified against configured
"limits" file. The limits are applied by processes performing specific quality calculations.

The results is a detail report of calculated values. The indexes of slices that did not pass
quality check are returned back.

"""
import numpy as np
import struct as st
import array as ar

__author__ = "Barbara Frosik"
__copyright__ = "Copyright (c) 2016, UChicago Argonne, LLC."
__docformat__ = 'restructuredtext en'
__all__ = ['init',
           'verify_file_hdf',
           'verify_file_ge',
           'verify']


class File_reader:
    def get_frame(self):
        pass


class Tif_fr(File_reader):

    def get_frame(self, filename):
        image = None
        File = open(filename, 'rb')
        dataType = 5
        try:
            Meta = open(filename + '.metadata', 'r')
            while True:
                line = Meta.readline()
                if line.startswith('dataType'):
                    dataType = int(line.split('=')[1])
                    break
            Meta.close()
        except IOError:
            print('no metadata file found - will try to read file anyway')

        tag = File.read(2)
        if 'bytes' in str(type(tag)):
            tag = tag.decode('latin-1')
        byteOrd = '<'
        if tag == 'II' and int(st.unpack('<h', File.read(2))[0]) == 42:  # little endian
            IFD = int(st.unpack(byteOrd + 'i', File.read(4))[0])
        elif tag == 'MM' and int(st.unpack('>h', File.read(2))[0]) == 42:  # big endian
            byteOrd = '>'
            IFD = int(st.unpack(byteOrd + 'i', File.read(4))[0])
        else:
            print('not a detector tiff file')
            return None

        File.seek(IFD)  # get number of directory entries
        NED = int(st.unpack(byteOrd + 'h', File.read(2))[0])
        IFD = {}
        nSlice = 1
        for ied in range(NED):
            Tag, Type = st.unpack(byteOrd + 'Hh', File.read(4))
            nVal = st.unpack(byteOrd + 'i', File.read(4))[0]
            if Type == 1:
                Value = st.unpack(byteOrd + nVal * 'b', File.read(nVal))
            elif Type == 2:
                Value = st.unpack(byteOrd + 'i', File.read(4))
            elif Type == 3:
                Value = st.unpack(byteOrd + nVal * 'h', File.read(nVal * 2))
                st.unpack(byteOrd + nVal * 'h', File.read(nVal * 2))
            elif Type == 4:
                if Tag in [273, 279]:
                    nSlice = nVal
                    nVal = 1
                Value = st.unpack(byteOrd + nVal * 'i', File.read(nVal * 4))
            elif Type == 5:
                Value = st.unpack(byteOrd + nVal * 'i', File.read(nVal * 4))
            elif Type == 11:
                Value = st.unpack(byteOrd + nVal * 'f', File.read(nVal * 4))
            IFD[Tag] = [Type, nVal, Value]
        sizexy = [IFD[256][2][0], IFD[257][2][0]]
        [nx, ny] = sizexy
        Npix = nx * ny
        if 34710 in IFD:
            print('MAR CCD tiff format not supported')
            return None
        elif nSlice > 1:  # CheMin multislice tif file!
            try:
                import Image as Im
            except ImportError:
                try:
                    from PIL import Image as Im
                except ImportError:
                    print("PIL/pillow Image module not present. This TIF cannot be read without this")
                    print('not a detector tiff file')
                    return None

            tifType = 'CheMin'
            image = np.flipud(np.array(Im.open(filename))) * 10.
        elif 272 in IFD:
            ifd = IFD[272]
            File.seek(ifd[2][0])
            S = File.read(ifd[1])
            if b'PILATUS' in S:
                tifType = 'Pilatus'
                dataType = 0
                File.seek(4096)
                print('Read Pilatus tiff file: ' + filename)
                image = np.array(np.frombuffer(File.read(4 * Npix), dtype=np.int32), dtype=np.int32)
            else:
                if IFD[258][2][0] == 16:
                    if sizexy == [3888, 3072] or sizexy == [3072, 3888]:
                        tifType = 'Dexela'
                        print('Read Dexela detector tiff file: ' + filename)
                    else:
                        tifType = 'GE'
                        print('Read GE-detector tiff file: ' + filename)
                    File.seek(8)
                    image = np.array(np.frombuffer(File.read(2 * Npix), dtype=np.uint16), dtype=np.int32)
                elif IFD[258][2][0] == 32:
                    # includes CHESS & Pilatus files from Area Detector
                    tifType = 'CHESS'
                    File.seek(8)
                    print('Read as 32-bit unsigned (CHESS) tiff file: ' + filename)
                    image = np.array(ar.array('I', File.read(4 * Npix)), dtype=np.uint32)
        elif 270 in IFD:
            File.seek(IFD[270][2][0])
            S = File.read(IFD[273][2][0] - IFD[270][2][0])
            if b'ImageJ' in S:
                tifType = 'ImageJ'
                dataType = 0
                File.seek(IFD[273][2][0])
                print('Read ImageJ tiff file: ' + filename)
                if IFD[258][2][0] == 32:
                    image = File.read(4 * Npix)
                    image = np.array(np.frombuffer(image, dtype=byteOrd + 'i4'), dtype=np.int32)
                elif IFD[258][2][0] == 16:
                    image = File.read(2 * Npix)
                    image = np.array(np.frombuffer(image, dtype=byteOrd + 'u2'), dtype=np.int32)
            else:  # gain map from  11-ID-C?
                tifType = 'Gain map'
                image = File.read(4 * Npix)
                image = np.array(np.frombuffer(image, dtype=byteOrd + 'f4') * 1000, dtype=np.int32)

        elif 262 in IFD and IFD[262][2][0] > 4:
            tifType = 'DND'
            File.seek(512)
            print('Read DND SAX/WAX-detector tiff file: ' + filename)
            image = np.array(np.frombuffer(File.read(2 * Npix), dtype=np.uint16), dtype=np.int32)
        elif sizexy == [1536, 1536]:
            tifType = 'APS Gold'
            File.seek(64)
            print('Read Gold tiff file:' + filename)
            image = np.array(np.frombuffer(File.read(2 * Npix), dtype=np.uint16), dtype=np.int32)
        elif sizexy == [2048, 2048] or sizexy == [1024, 1024] or sizexy == [3072, 3072]:
            if IFD[273][2][0] == 8:
                if IFD[258][2][0] == 32:
                    tifType = 'PE'
                    File.seek(8)
                    print('Read APS PE-detector tiff file: ' + filename)
                    if dataType == 5:
                        image = np.array(np.frombuffer(File.read(4 * Npix), dtype=np.float32),
                                         dtype=np.int32)  # fastest
                    else:
                        image = np.array(np.frombuffer(File.read(4 * Npix), dtype=np.int32), dtype=np.int32)
                elif IFD[258][2][0] == 16:
                    tifType = 'MedOptics D1'
                    File.seek(8)
                    print('Read MedOptics D1 tiff file: ' + filename)
                    image = np.array(np.frombuffer(File.read(2 * Npix), dtype=np.uint16), dtype=np.int32)

        elif IFD[273][2][0] == 4096:
            if sizexy[0] == 3072:
                tifType = 'MAR225'
            else:
                tifType = 'MAR325'
            File.seek(4096)
            print('Read MAR CCD tiff file: ' + filename)
            image = np.array(np.frombuffer(File.read(2 * Npix), dtype=np.uint16), dtype=np.int32)
        elif IFD[273][2][0] == 512:
            tifType = '11-ID-C'
            File.seek(512)
            print('Read 11-ID-C tiff file: ' + filename)
            image = np.array(np.frombuffer(File.read(2 * Npix), dtype=np.uint16), dtype=np.int32)

        elif sizexy == [4096, 4096]:
            if IFD[273][2][0] == 8:
                if IFD[258][2][0] == 16:
                    tifType = 'scanCCD'
                    File.seek(8)
                    print('Read APS scanCCD tiff file: ' + filename)
                    image = np.array(ar.array('H', File.read(2 * Npix)), dtype=np.int32)
                elif IFD[258][2][0] == 32:
                    tifType = 'PE4k'
                    File.seek(8)
                    print('Read PE 4Kx4K tiff file: ' + filename)
                    image = np.array(np.frombuffer(File.read(4 * Npix), dtype=np.float32) / 2. ** 4, dtype=np.int32)
            elif IFD[273][2][0] == 4096:
                tifType = 'Rayonix'
                File.seek(4096)
                print('Read Rayonix MX300HE tiff file: ' + filename)
                image = np.array(np.frombuffer(File.read(2 * Npix), dtype=np.uint16), dtype=np.int32)
        elif sizexy == [391, 380]:
            File.seek(8)
            image = np.array(np.frombuffer(File.read(2 * Npix), dtype=np.int16), dtype=np.int32)
        elif sizexy == [380, 391]:
            File.seek(110)
            image = np.array(np.frombuffer(File.read(Npix), dtype=np.uint8), dtype=np.int32)
        elif sizexy == [825, 830]:
            File.seek(8)
            image = np.array(np.frombuffer(File.read(Npix), dtype=np.uint8), dtype=np.int32)
        elif sizexy == [1800, 1800]:
            File.seek(110)
            image = np.array(np.frombuffer(File.read(Npix), dtype=np.uint8), dtype=np.int32)
        elif sizexy == [2880, 2880]:
            File.seek(8)
            dt = np.dtype(np.float32)
            dt = dt.newbyteorder(byteOrd)
            image = np.array(np.frombuffer(File.read(Npix * 4), dtype=dt), dtype=np.int32)
        elif sizexy == [3070, 1102]:
            print('Read Dectris Eiger 1M tiff file: ' + filename)
            File.seek(8)
            dt = np.dtype(np.float32)
            dt = dt.newbyteorder(byteOrd)
            image = np.array(np.frombuffer(File.read(Npix * 4), dtype=np.uint32), dtype=np.int32)

        if image is None:
            print('not a known detector tiff file')
            return None

        if sizexy[1] * sizexy[0] != image.size:  # test is resize is allowed
            print('not a known detector tiff file')
            return None

        image = np.reshape(image, (sizexy[1], sizexy[0]))

        File.close()
        #        print('image', image.shape)
        return image
