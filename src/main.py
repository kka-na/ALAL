'''
1) when resource modified
pyrcc5 -o resources_rc.py resources.qrc
2) when ui modified
pyuic5 -o mainwindow.py mainwindow.ui
'''

#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, shutil, os
from pathlib import Path

from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from mainwindow import Ui_MainWindow

import getdata
import resources_rc

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.gt_label = QLabel()
        self.net_label = QLabel()
        self.at_label = QLabel()
        self.make_new = None
        self.storage = ""
        self.dir = ""
        self.movie = QMovie()
        self.mode = None
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.ui.radioInf.clicked.connect(self.set_mode)
        self.ui.radioAuto.clicked.connect(self.set_mode)
        self.getData = None

    def set_mode(self):
        if self.ui.radioInf.isChecked():
            self.mode = 0
            self.getData = getdata.GetData()
            self.getData.mode = self.mode
            self.set_layout0()

        elif self.ui.radioAuto.isChecked():
            self.mode = 1
            self.getData = getdata.GetData()
            self.getData.mode = self.mode
            self.set_layout1()
        self.set_connect()

        self.test = False
        if self.test:
            self.set_data()
            self.set_storage()

    def set_layout0(self):
        self.gt_label = QLabel()
        self.gt_label.setAlignment(Qt.AlignCenter)
        self.ui.gtLayout.addWidget(self.gt_label)
        self.net_label = QLabel()
        self.net_label.setAlignment(Qt.AlignCenter)
        self.ui.netLayout.addWidget(self.net_label)

    def set_layout1(self):
        self.at_label = QLabel()
        self.at_label.setAlignment(Qt.AlignCenter)
        self.ui.atLayout.addWidget(self.at_label)

    def set_connect(self):
        self.ui.dataButton.clicked.connect(self.set_data)
        self.ui.storageButton.clicked.connect(self.set_storage)
        self.ui.leftButton.clicked.connect(self.go_left)
        self.ui.rightButton.clicked.connect(self.go_right)
        self.ui.matchButton.clicked.connect(self.getData.calc.calc_start)
        self.ui.matchButton.clicked.connect(self.matching)
        self.ui.saveOnceButton.clicked.connect(self.getData.calc.save_once)
        self.ui.iouSpin.valueChanged.connect(self.value_changed)
        self.ui.confSpin.valueChanged.connect(self.value_changed)
        self.getData.send_list.connect(self.disp_list)
        self.getData.send_len.connect(self.disp_len)
        self.getData.send_name.connect(self.disp_name)
        self.getData.send_img0.connect(self.disp_img0)
        self.getData.send_img1.connect(self.disp_img1)
        self.getData.send_img2.connect(self.disp_img2)
        self.getData.calc.send_miou.connect(self.disp_miou)
        self.getData.calc.send_mconf.connect(self.disp_mconf)
        self.getData.calc.send_conf_th.connect(self.disp_conf_th)
        self.getData.calc.send_conf_th.connect(self.stop_matching)

    def set_data(self):
        if self.test:
            path = "/home/kana/Documents/AutoLabeling/data/2DOD"
        else:
            path = QFileDialog.getExistingDirectory(None, 'Select Directory of top of datasets', QDir.currentPath(),
                                                    QFileDialog.ShowDirsOnly)
        self.dir = str(path)
        self.set_variables()
        self.getData.set_path(self.dir)

    def set_variables(self):
        if os.path.isfile(str(Path(self.dir).parent)+"/log.txt"):
            self.getData.calc.iou_th = self.ui.iouSpin.value() / 100.0
            with open(str(Path(self.dir).parent)+"/log.txt") as f:
                for line in f:
                    pass
                last_line = line
            val = line.split()
            self.getData.calc.conf_th = float(val[2])
            self.ui.confSpin.setValue(int(float(val[2])*100))
        else:
            self.getData.calc.iou_th = self.ui.iouSpin.value() / 100.0
            self.getData.calc.conf_th = self.ui.confSpin.value() / 100.0

    def value_changed(self):
        self.getData.calc.iou_th = self.ui.iouSpin.value() / 100.0
        self.getData.calc.conf_th = self.ui.confSpin.value() / 100.0

    def set_storage(self):
        if self.test:
            path = "/home/kana/Documents/AutoLabeling/data/2DOD/classified"
        else:
            path = QFileDialog.getExistingDirectory(None, 'Select Directory of store classified result',
                                                    QDir.currentPath(), QFileDialog.ShowDirsOnly)
        self.storage = str(path)
        self.getData.calc.storage = self.storage
        self.create_dir()

    def create_dir(self):
        self.make_new = False
        high = str(self.storage + "/high")
        low = str(self.storage + "/low")
        high_data = str(high + "/data")
        high_label = str(high + "/label")
        low_data = str(low + "/data")
        low_label = str(low + "/label")

        if self.test:
            self.make_new = True
            self.make_dir(high)
            self.make_dir(low)
        else:
            mbox = QMessageBox()
            mbox.setWindowTitle("Create New Directory")
            mbox.setText("Create a Directory to Save.     \nCreate or Not?     ")
            mbox.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
            buttonC = mbox.button(QMessageBox.Ok)
            buttonC.setText('Create')
            returnv = mbox.exec_()
            if returnv == QMessageBox.Ok:
                self.make_new = True
                self.make_dir(high)
                self.make_dir(low)
            else:
                sys.exit()

        self.make_dir(high_data)
        self.make_dir(high_label)
        self.make_dir(low_data)
        self.make_dir(low_label)

    def make_dir(self, path):
        if not os.path.exists(path):
            os.mkdir(path)
        else:
            if self.make_new:
                shutil.rmtree(path)
                os.mkdir(path)
            else:
                print("There is No Permission to Create Top Directory")
                sys.exit()

    def go_left(self):
        self.getData.move(-1)

    def go_right(self):
        self.getData.move(1)

    def disp_list(self, _object):
        for i in _object:
            item = QListWidgetItem(i)
            self.ui.dataList.addItem(item)

    def disp_len(self, _object):
        self.ui.informationLabel.setText(str(_object))

    def disp_name(self, _object):
        self.ui.imgName.setText("  " + str(_object))

    def disp_img0(self, _object):
        self.gt_label.setPixmap(
            QPixmap.fromImage(_object).scaled(self.gt_label.width(), self.gt_label.height(), aspectRatioMode=0))
        QCoreApplication.processEvents()

    def disp_img1(self, _object):
        self.net_label.setPixmap(
            QPixmap.fromImage(_object).scaled(self.net_label.width(), self.net_label.height(), aspectRatioMode=0))
        QCoreApplication.processEvents()
    
    def disp_img2(self, _object):
        self.at_label.setPixmap(
            QPixmap.fromImage(_object).scaled(self.at_label.width(), self.at_label.height(), aspectRatioMode=0))
        QCoreApplication.processEvents()

    def disp_miou(self, _object):
        self.ui.mIoULabel.setText("mIoU = " + str(round(_object, 3)) + "%")

    def disp_mconf(self, _object):
        if self.mode == 0:
            self.ui.mConfLabel.setText("mConf = " + str(round(_object, 3)) + "%")
        elif self.mode == 1:
            self.ui.mConfLabel2.setText("mConf = " + str(round(_object, 3)) + "%")

    def disp_conf_th(self, _object):
        self.ui.confThLabel_2.setText("θ = " + str(round(_object, 3)) + "%")

    def matching(self):
        self.movie = QMovie(":/icon/icon.gif", QByteArray())
        self.ui.AL.setMovie(self.movie)
        self.movie.start()

    def stop_matching(self, _ ):
        self.movie.stop()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    mainWindow = MainWindow()
    mainWindow.show()
    sys.exit(app.exec_())
