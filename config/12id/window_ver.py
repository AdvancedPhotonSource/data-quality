import sys
import os
from os.path import expanduser
from configobj import ConfigObj
import json
import epics
from PyQt4 import QtGui, uic
from PyQt4.QtCore import pyqtSignal, pyqtSlot
from multiprocessing import Process
import dquality.realtime.real_time as real
import zmq


class zmq_sen():
    def __init__(self, port=5511):
        context = zmq.Context()
        self.socket = context.socket(zmq.PAIR)
        self.socket.bind("tcp://*:%s" % port)


class Window(QtGui.QMainWindow):
    statusBarSignal = pyqtSignal(str, str)

    def __init__(self):
        super(Window, self).__init__()
        self.ui = uic.loadUi("verui.ui")
        self.ui.show()

        self.detector = "S12-PILATUS1"
        self.show_limits()
        self.ui.det_name.setText(self.detector)

        self.ui.det_name.returnPressed.connect(lambda: self.set_detector())

        self.ui.frame_sum_ll.returnPressed.connect(lambda: self.set_limit(self.ui.frame_sum_ll, 'sum','low_limit'))
        self.ui.frame_sum_hl.returnPressed.connect(lambda: self.set_limit(self.ui.frame_sum_hl, 'sum','high_limit'))
        self.ui.point_sat_hl.returnPressed.connect(lambda: self.set_limit(self.ui.point_sat_hl, 'sat','high_limit'))
        self.ui.frame_sat_points_hl.returnPressed.connect(lambda: self.set_limit(self.ui.frame_sat_points_hl, 'frame_sat','high_limit'))
        self.ui.rate_ll.returnPressed.connect(lambda: self.set_limit(self.ui.rate_ll, 'rate_sat','low_limit'))
        self.ui.rate_hl.returnPressed.connect(lambda: self.set_limit(self.ui.rate_hl, 'rate_sat','high_limit'))

        self.setEpicsQualityFeedbackUpdate()

        self.ui.actionStart_verifier.triggered.connect(self.start_verifier)
        self.ui.actionStop_verifier.triggered.connect(self.stop_verifier)

        self.ui.statusBar.showMessage("verifier off")
        self.statusBarSignal.connect(self.onVerifierPVchange)
        self.zmq_menu = zmq_sen()


    def start_verifier(self):
        print 'starting ver, conf', self.conf
        socket = self.zmq_menu.socket
        socket.send_json(
            dict(
                key="start_ver",
                detector=self.detector
            )
        )

    def stop_verifier(self):
        print 'stopping ver'
        socket = self.zmq_menu.socket
        socket.send_json(
            dict(
                key="stop_ver"
            )
        )

    def set_detector(self):
        self.detector = str(self.ui.det_name.text())
        self.show_limits()


    def show_limits(self):
        home = expanduser("~")
        self.conf = os.path.join(home, '.dquality', self.detector)
        if os.path.isdir(self.conf):
            config = os.path.join(self.conf, 'dqconfig.ini')
        if not os.path.isfile(config):
            return None
        conf_map = ConfigObj(config)
        try:
            self.limits_file = conf_map['limits']
        except KeyError:
            self.limits_file = None

        with open(self.limits_file) as limitsfile:
            self.limits = json.loads(limitsfile.read())['data']
            self.ui.frame_sum_ll.setText(str(self.limits['sum']['low_limit']))
            self.ui.frame_sum_hl.setText(str(self.limits['sum']['high_limit']))
            self.ui.point_sat_hl.setText(str(self.limits['sat']['high_limit']))
            self.ui.frame_sat_points_hl.setText(str(self.limits['frame_sat']['high_limit']))
            self.ui.rate_ll.setText(str(self.limits['rate_sat']['low_limit']))
            self.ui.rate_hl.setText(str(self.limits['rate_sat']['high_limit']))
        limitsfile.close()


    def set_limit(self, le_limit, key1, key2):
        limit_val = int(le_limit.text())
        self.limits[key1][key2] = limit_val
        data_limits = {}
        data_limits['data'] = self.limits
        with open(self.limits_file, 'w') as limitsfile:
            json.dump(data_limits, limitsfile)
        limitsfile.close()


    def setEpicsQualityFeedbackUpdate(self):
        try:
            self.ver = epics.PV(self.detector + ':ver', callback=self.epicsCallbackFunc)
            print 'set callback', self.ver
        except:
            self.ui.statusBar.showMessage('verifier off')


    def epicsCallbackFunc(self, pvname, char_value, **kws):
        self.statusBarSignal.emit(pvname, char_value)


    @pyqtSlot(str, str)
    def onVerifierPVchange(self, pvname, char_value):
        if not pvname is None:
            if "ver" in pvname:
                if int(float(char_value)) is 0:
                    self.ui.statusBar.setStyleSheet(
                        "QStatusBar{padding-left:8px;background:rgba(0,255,0,120);color:black;font-weight:bold;}")
                    msg = 'verification pass'
                elif int(float(char_value)) is 1:
                    self.ui.statusBar.setStyleSheet(
                        "QStatusBar{padding-left:8px;background:rgba(255,0,0,120);color:black;font-weight:bold;}")
                    msg = 'verification failed'
                elif int(float(char_value)) is -1:
                    self.ui.statusBar.setStyleSheet(
                        "QStatusBar{padding-left:8px;background:rgba(255,255,0,120);color:black;font-weight:bold;}")
                    msg = 'not acquireing'
                self.ui.statusBar.showMessage(msg)
        else:
            self.ui.statusBar.showMessage("ver pv name not defined")



if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    a = Window()
    sys.exit(app.exec_())
