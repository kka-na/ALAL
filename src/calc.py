import os
import shutil
from datetime import datetime
from operator import itemgetter
from PyQt5.QtCore import *
from pathlib import Path

class Calc(QObject):
    def __init__(self):
        super(Calc, self).__init__()
        self.mode = None
        self.path = ""
        self.gt_data = ""
        self.gt_data_paths = []
        self.gt_label = ""
        self.gt_label_paths = []
        self.data_len = 0
        self.net_data = ""
        self.net_label = ""
        self.auto_data = ""
        self.auto_data_paths = []
        self.auto_label = ""
        self.auto_label_paths = []
        self.storage = ""
        self.now_img_name = ""
        self.now_label_name = ""
        self.width = 0
        self.height = 0
        self.class_num = 0
        self.means = []
        self.conf_th = 0
        self.iou_th = 0

    send_mconf = pyqtSignal(object)
    send_miou = pyqtSignal(object)

    def calc_mean(self):
        if self.mode == 0:
            mconf, miou = self.calc_means(self.gt_label + self.now_label_name, self.net_label + self.now_label_name)
            self.send_miou.emit(miou * 100.0)
        elif self.mode == 1:
            auto_bboxes = self.get_label_list(2, self.auto_label + self.now_label_name)
            mconf = self.calc_mconf(auto_bboxes)
        self.send_mconf.emit(mconf * 100.0)

    send_conf_th = pyqtSignal(object)

    def calc_start(self):
        conf_sum = 0.0
        iou_sum = 0.0

        self.means = []
        high_conf_cont = 0
        for i in range(self.data_len):
            if self.mode == 0:
                mconf, miou = self.calc_means(self.gt_label + self.gt_data_paths[i].split(".")[0]+".txt",
                                            self.net_label + self.gt_data_paths[i].split(".")[0]+".txt")
                iou_sum += miou
                if miou >= self.iou_th:
                    conf_sum += mconf
                    high_conf_cont += 1
            elif self.mode == 1:
                auto_bboxes = self.get_label_list(2, self.auto_label + self.auto_data_paths[i].split(".")[0]+".txt")
                mconf = self.calc_mconf(auto_bboxes)
                conf_sum += mconf
                self.means.append([str(self.auto_data_paths[i]), str(self.auto_data_paths[i].split(".")[0]+".txt"), mconf])

        if self.mode == 0:
            conf_sum /= high_conf_cont
            self.send_conf_th.emit(conf_sum * 100.0)
            iou_sum /= self.data_len
            now_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S ')
            log_path = str(Path(self.path).parent)+"/log.txt"
            if os.path.isfile(log_path):
                f = open(log_path, 'a')
                f.write("\n" + now_time + str(conf_sum) + " " + str(iou_sum))
                f.close()
            else:
                f = open(log_path, 'w')
                f.write("whole_files mean_confidence mean_iou\n")
                f.write(now_time + str(conf_sum) + " " + str(iou_sum))
                f.close()
        elif self.mode == 1:
            conf_sum /= self.data_len
            self.send_conf_th.emit(conf_sum * 100.0)

    def save_once(self):
        f = open(self.storage + "/result_list.txt", 'w')
        f.write("uncertainty(0:low, 1:high) data_name label_name mean_confidence\n")
        i = 0
        for mean in self.means:
            if self.mode == 0:
                src1 = self.gt_data + mean[0]
                src2 = self.net_label + mean[1]
            elif self.mode == 1:
                src1 = self.auto_data + mean[0]
                src2 = self.auto_label + mean[1]
            uncertainty = self.calc_uncertainty(mean)
            if uncertainty == 0:
                shutil.copy2(src1, self.storage + "/low/data/" + mean[0])
                if os.path.isfile(src2):
                    shutil.copy2(src2, self.storage + "/low/label/" + mean[1])
            elif uncertainty == 1:
                shutil.copy2(src1, self.storage + "/high/data/" + mean[0])
                if os.path.isfile(src2):
                    shutil.copy2(src2, self.storage + "/high/label/" + mean[1])
            f.write(str(uncertainty) + " " + mean[0] + " " + mean[1] + " " + str(mean[2]))
            if i < len(self.means) - 1:
                f.write("\n")
            i += 1
        f.close()

    def calc_uncertainty(self, mean):
        _type = 0  # need a human labeling : 0 , auto labeled  : 1
        if mean[2] >= self.conf_th:
            _type = 1
        return _type

    def calc_means(self, gt_path, net_path):
        gt_bboxes = self.get_label_list(0, gt_path)
        net_bboxes = self.get_label_list(1, net_path)
        mconf = self.calc_mconf(net_bboxes)
        ious = self.calc_ious(gt_bboxes, net_bboxes)
        miou = self.calc_mious(ious)
        return mconf, miou

    def calc_mconf(self, bboxes):
        conf = 0.0
        for bbox in bboxes:
            conf += bbox['conf']
        return conf / (len(bboxes) + 1e-9)

    def calc_mious(self, ious):
        iou_sum = 0.0
        for i in range(len(ious)):
            iou_sum += float(list(ious[i].values())[0])
        if iou_sum <= 0.0:
            miou = 0.0
        else:
            miou = iou_sum / float(len(ious) + 1e-9)
        return miou

    def calc_ious(self, gt_bboxes, net_bboxes):
        ious = []
        checked_gt = []
        for i in range(len(net_bboxes)):
            each_ious = {}
            for j in range(len(gt_bboxes)):
                iou = {int(j): float(self.calc_iou(gt_bboxes[j], net_bboxes[i]))}
                each_ious.update(iou)
            each_ious = sorted(each_ious.items(), key=lambda x: x[1], reverse=True)
            iou = 0.0
            if i == 0:
                iou = each_ious[0][1]
                checked_gt.append(each_ious[0][0])
            else:
                for k in range(len(checked_gt)):
                    if each_ious[0][0] == checked_gt[k]:
                        iou = 0.0
                    else:
                        iou = each_ious[0][1]
                        checked_gt.append(each_ious[0][0])
                        break
            ious.append({int(net_bboxes[i]['cls']): float(iou)})
        return ious

    def calc_iou(self, gt_bbox, net_bbox):
        x1 = max(gt_bbox['bbox'][0], net_bbox['bbox'][0])
        y1 = max(gt_bbox['bbox'][1], net_bbox['bbox'][1])
        x2 = min(gt_bbox['bbox'][2], net_bbox['bbox'][2])
        y2 = min(gt_bbox['bbox'][3], net_bbox['bbox'][3])
        tmp_width = x2 - x1
        tmp_height = y2 - y1
        iou = 0.0
        if tmp_width < 0 or tmp_height < 0:
            iou = 0.0
            return iou
        overlap = tmp_width * tmp_height
        a = (gt_bbox['bbox'][2] - gt_bbox['bbox'][0]) * (gt_bbox['bbox'][3] - gt_bbox['bbox'][1])
        b = (net_bbox['bbox'][2] - net_bbox['bbox'][0]) * (net_bbox['bbox'][3] - net_bbox['bbox'][1])
        combine = a + b - overlap
        iou = float(overlap / (combine + 1e-5))
        return iou

    def get_label_list(self, _type, file):
        bboxes = []
        if os.path.isfile(file):
            fr = open(file)
            lines = fr.readlines()
            for line in lines:
                val = line.split()
                if _type == 0:
                    conf = 1.0
                    calc_box = self.calc_boxes(val[1:])
                    _center = [float(val[1]) * self.width, float(val[2]) * self.height]
                else:
                    conf = float(val[1])
                    calc_box = self.calc_boxes(val[2:])
                    _center = [float(val[2]) * self.width, float(val[3]) * self.height]
                bbox = {'cls': val[0], 'conf': conf, 'size': calc_box[0:2], 'bbox': calc_box[2:], 'center': _center}
                bboxes.append(bbox)

        bboxes = sorted(bboxes, key=itemgetter('conf'), reverse=True)
        return bboxes

    def calc_boxes(self, _object):
        lx = (float(_object[0]) - float(_object[2]) / 2) * self.width
        ly = (float(_object[1]) - float(_object[3]) / 2) * self.height
        rx = (float(_object[0]) + float(_object[2]) / 2) * self.width
        ry = (float(_object[1]) + float(_object[3]) / 2) * self.height
        return [float(_object[2]) * self.width, float(_object[3]) * self.height, lx, ly, rx, ry]
