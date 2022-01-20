import os
from pathlib import Path

from PyQt5.QtCore import *
from PyQt5.QtGui import *

import calc


class GetData(QObject):
    def __init__(self):
        super(GetData, self).__init__()
        self.mode = None
        self.gt_data = ""
        self.gt_data_paths = []
        self.data_len = 0
        self.gt_label = ""
        self.gt_label_paths = []
        self.net_data = ""
        self.net_label = ""
        self.now_idx = 0
        self.now_img_name = ""
        self.now_label_name = ""
        self.auto_data = ""
        self.auto_data_paths = []
        self.data_len = 0
        self.auto_label = ""
        self.auto_label_paths = []
        self.class_list = []
        self.width = 0
        self.height = 0

        self.calc = calc.Calc()

    send_list = pyqtSignal(object)
    send_len = pyqtSignal(object)

    def set_path(self, path):
        self.calc.mode = self.mode

        if self.mode == 0:
            self.calc.path = path
            self.gt_data = path + "/gt/data/"
            self.gt_data_paths = []
            self.gt_data_paths.extend(os.path.basename(x) for x in sorted(Path(self.gt_data).glob("*.jpg")))
            self.gt_data_paths.extend(os.path.basename(x) for x in sorted(Path(self.gt_data).glob("*.png")))
            self.data_len = len(self.gt_data_paths)
            self.send_list.emit(self.gt_data_paths)
            self.send_len.emit(self.data_len)
            self.gt_label = path + "/gt/label/"
            self.gt_label_paths = []
            self.gt_label_paths.extend(os.path.basename(x) for x in sorted(Path(self.gt_label).glob("*.txt")))
            self.net_data = path + "/net/data/"
            self.net_label = path + "/net/label/"

            self.calc.gt_data = self.gt_data
            self.calc.gt_data_paths = self.gt_data_paths
            self.calc.gt_label = self.gt_label
            self.calc.gt_label_paths = self.gt_label_paths
            self.calc.data_len = self.data_len
            self.calc.net_data = self.net_data
            self.calc.net_label = self.net_label
            self.now_idx = 0
            self.now_img_name = self.gt_data_paths[self.now_idx]
            
        elif self.mode == 1:
            self.calc.path = path
            self.auto_data = path + "/auto/data/"
            self.auto_data_paths = []
            self.auto_data_paths.extend(os.path.basename(x) for x in sorted(Path(self.auto_data).glob("*.jpg")))
            self.auto_data_paths.extend(os.path.basename(x) for x in sorted(Path(self.auto_data).glob("*.png")))
            self.data_len = len(self.auto_data_paths)
            self.send_list.emit(self.auto_data_paths)
            self.send_len.emit(self.data_len)
            self.auto_label = path + "/auto/label/"
            self.auto_label_paths = []
            self.auto_label_paths.extend(os.path.basename(x) for x in sorted(Path(self.auto_label).glob("*.txt")))
            self.calc.auto_data = self.auto_data
            self.calc.auto_data_paths = self.auto_data_paths
            self.calc.auto_label = self.auto_label
            self.calc.auto_label_paths = self.auto_label_paths
            self.calc.data_len = self.data_len
            self.now_idx = 0
            self.now_img_name = self.auto_data_paths[self.now_idx]
            
        self.now_label_name = self.now_img_name.split(".")[0]+".txt"
        self.calc.now_idx = self.now_idx
        self.calc.now_img_name = self.now_img_name
        self.calc.now_label_name = self.now_label_name
        fr = open(str(path + "/classes.txt"))
        lines = fr.readlines()
        self.class_list = []
        for line in lines:
            self.class_list.append(line)
        self.calc.class_num = len(self.class_list)
        self.send_datum()

    send_name = pyqtSignal(object)

    def send_datum(self):
        self.send_name.emit(self.now_img_name)
        if self.mode == 0:
            self.send_img(0)
            self.send_img(1)
        elif self.mode == 1:
            self.send_img(2)
        self.calc.calc_mean()

    send_img0 = pyqtSignal(object)
    send_img1 = pyqtSignal(object)
    send_img2 = pyqtSignal(object)

    def send_img(self, _type):
        if self.mode == 0:
            img = QImage(str(self.gt_data) + self.now_img_name)
        elif self.mode == 1:
            img = QImage(str(self.auto_data) + self.now_img_name)
        self.width = img.width()
        self.height = img.height()
        self.calc.width = self.width
        self.calc.height = self.height
        if _type == 0:
            bboxes = self.calc.get_label_list(0, self.gt_label+self.now_label_name)
            img = self.draw_boxes(img, bboxes)
            self.send_img0.emit(img)
        elif _type == 1:
            bboxes = self.calc.get_label_list(1, self.net_label+self.now_label_name)
            img = self.draw_boxes(img, bboxes)
            self.send_img1.emit(img)
        elif _type == 2:
            bboxes = self.calc.get_label_list(2, self.auto_label+self.now_label_name)
            img = self.draw_boxes(img, bboxes)
            self.send_img2.emit(img)

    def draw_boxes(self, img, bboxes):
        if len(bboxes) > 0:
            painter = QPainter(img)
            f = QFont("Helvetica [Cronyx]", img.height() / 30)
            for bbox in bboxes:
                pen = self.get_bbox_pen(int(bbox['cls']))
                painter.setPen(pen)
                qrect = QRect(bbox['bbox'][0], bbox['bbox'][1], bbox['size'][0], bbox['size'][1])
                painter.drawRect(qrect)
                painter.setFont(f)
                class_name = self.class_list[int(bbox['cls'])]
                painter.drawText(bbox['bbox'][0], bbox['bbox'][1] - 10, class_name)
            painter.end()
        return img

    def get_bbox_pen(self, _object):
        pen = QPen()
        pen.setWidth(5)
        if _object % 6 == 0:
            qb = QBrush(QColor('yellow'))
            pen.setBrush(qb)
        elif _object % 6 == 1:
            qb = QBrush(QColor('magenta'))
            pen.setBrush(qb)
        elif _object % 6 == 2:
            qb = QBrush(QColor('cyan'))
            pen.setBrush(qb)
        elif _object % 6 == 3:
            qb = QBrush(QColor('red'))
            pen.setBrush(qb)
        elif _object % 6 == 4:
            qb = QBrush(QColor('blue'))
            pen.setBrush(qb)
        else:
            qb = QBrush(QColor('green'))
            pen.setBrush(qb)
        return pen

    def move(self, idx):
        self.now_idx += idx
        if self.now_idx < 0:
            self.now_idx = 0
        elif self.now_idx > self.data_len - 1:
            self.now_idx = self.data_len - 1

        if self.mode == 0:
            self.now_img_name = self.gt_data_paths[self.now_idx]
        elif self.mode == 1:
            self.now_img_name = self.auto_data_paths[self.now_idx]

        self.now_label_name = self.now_img_name.split(".")[0]+".txt"
        self.calc.now_img_name = self.now_img_name
        self.calc.now_label_name = self.now_label_name
        self.send_datum()
