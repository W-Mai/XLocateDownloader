# Copyright (c) 2021 W-Mai
# 
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

from contextlib import closing

import requests
from PyQt6.QtCore import *
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
import PyQt6.sip
import sys
import os
import json
from typing import *
import threading
from time import sleep
from random import random

mutex = threading.Lock()
mutex_ps = threading.Lock()


def abstract_file_path(file):
    return file.lstrip('/')


def check_file_valid(file):
    if not os.path.isfile(file):
        return False
    print(file)
    with open(file, 'rb') as f:
        mg = f.read(8)
        print(mg)
        return mg == b'{"URL":{'


headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36'
}

timeout = 5


def download(img_url, img_name, out_dir):
    if os.path.isfile(os.path.join(out_dir, img_name)):
        return {'code': 1, 'msg': 'S:E'}
    with closing(requests.get(img_url, stream=True, headers=headers, timeout=timeout)) as r:
        rc = r.status_code
        if 299 < rc or rc < 200:
            return {'code': 1, 'msg': f'C:{rc}'}

        content_length = int(r.headers.get('content-length', '0'))
        if content_length == 0:
            return {'code': 1, 'msg': f'L:{0}'}
        try:
            if not os.path.exists(out_dir):
                os.makedirs(out_dir)
            with open(os.path.join(out_dir, img_name), 'wb') as f:
                for data in r.iter_content(1024):
                    f.write(data)
        except Exception as e:
            print(e)
            return {'code': 1, 'msg': 'S:F'}
    return {'code': 0, 'msg': None}


class EmptyDelegate(QItemDelegate):
    def __init__(self, parent):
        super(EmptyDelegate, self).__init__(parent)

    def createEditor(self, e1: QWidget, e2: QStyleOptionViewItem, e3: QModelIndex):
        return None


class MainWindow(QWidget):
    psSig = pyqtSignal()

    def __init__(self):
        super().__init__()

        self.TotalItem = 0
        self.CurrentFinished = 0
        self.setAcceptDrops(True)
        self.CurrentFilePath = ''
        self.tmpFilePath = ''
        self.CurrentDir = ''
        self.rawData = {}
        # 设置初始大小与标题

        # 垂直布局
        layout = QVBoxLayout()
        listview = QTableView()
        listview.setMinimumHeight(300)
        listview.setModel(QStandardItemModel(0, 2))
        listview.clicked.connect(self.clicked)
        listview.setItemDelegate(EmptyDelegate(self))
        listview.setColumnWidth(0, 150)
        listview.setColumnWidth(1, 80)
        self.model: QStandardItemModel = listview.model()
        self.model.setHorizontalHeaderLabels(["ＫＥＹ", "ＳＴＡＴＵＳ"])

        psProcess = QProgressBar()
        psProcess.setAlignment(Qt.Alignment.AlignCenter)
        psProcess.setValue(0)
        self.psProcess = psProcess

        btDownload = QPushButton()
        btDownload.setMinimumHeight(30)
        btDownload.setText("ＳＴＡＲＴ　ＤＯＷＮＬＯＡＤ")
        btDownload.clicked.connect(self.clicked_bt_download)
        layout.addWidget(listview)
        layout.addWidget(psProcess)
        layout.addWidget(btDownload)
        self.list = listview
        self.setLayout(layout)
        self.setUi()

    def setUi(self):
        self.setFixedWidth(300)
        self.setWindowTitle('XLocate Downloader')

        self.show()

    def dragEnterEvent(self, e: QDragEnterEvent):
        data: QMimeData = e.mimeData()
        urls = data.urls()
        if len(urls) == 1:
            path = abstract_file_path(urls[0].path())
            if check_file_valid(path):
                e.accept()
                self.tmpFilePath = path

            else:
                e.ignore()
        else:
            e.ignore()

    def dropEvent(self, e):
        self.CurrentFilePath = self.tmpFilePath
        # self.file_path = abstract_file_path(e.mimeData().urls()[0].path())
        self.list_clear()
        filename = os.path.split(self.CurrentFilePath)
        filename = os.path.splitext(filename[-1])[0]
        self.CurrentDir = os.path.join(os.path.dirname(self.CurrentFilePath), filename)
        print(self.CurrentDir)
        with open(self.CurrentFilePath) as f:
            self.rawData = json.load(f)
            print(self.rawData['URL'])
            self.list_insert_data(self.rawData['CODES'])

    def clicked(self, qModelIndex):
        print(qModelIndex.row())

    def clicked_bt_download(self, e):
        # url = "http://t0.tiles.ditu.live.com/tiles/r132122221.png?g=102&mkt=zh-cn&n=z"
        # print(download(url, 'test.png', r'C:\Users\W-Mai\Desktop\MAP'))
        if self.CurrentFilePath == "":
            return
        g = self.ItemGenerator()
        self.TotalItem = self.model.rowCount()
        self.CurrentFinished = 0
        self.psSig.connect(self.ProcessRefresh)
        # threading.Thread(target=self.ProcessRefreshThread).start()
        for index in range(32):
            threading.Thread(target=self.DownloadTread, args=(g,), name=str(index)).start()

    def list_insert_data(self, data: Dict[AnyStr, List[AnyStr]]):
        model = self.model
        for key, val in data.items():
            if int(key) < 10:
                continue
            model.appendRow(QStandardItem(f"{key}"))
            model.setItem(model.rowCount() - 1, 1, QStandardItem("..."))

    def list_clear(self):
        model = self.model
        model.removeRows(0, model.rowCount())

    def ProcessRefresh(self):
        # with mutex_ps:
        # print(int(self.CurrentFinished / self.TotalItem * 100))
        self.psProcess.setValue(int(self.CurrentFinished / self.TotalItem * 100))

    def ItemGenerator(self):
        model: QStandardItemModel = self.model
        prefix = self.rawData["URL"]['prefix']
        suffix = self.rawData["URL"]['suffix']
        num = model.rowCount()
        yield_list = []
        for index in range(num):
            key = model.data(model.index(index, 0), Qt.ItemDataRole.DisplayRole)
            url = prefix + key + suffix
            yield_list.append([index, key, url, self.rawData["CODES"][key]])
        for item in yield_list:
            yield item

    def ProcessRefreshThread(self):
        while True:
            try:
                self.ProcessRefresh()
            except Exception as e:
                print(e)

    def DownloadTread(self, g):

        while True:
            try:
                with mutex:
                    index, key, url, pos = next(g)
            except StopIteration:
                break
            model = self.model
            with mutex:
                print(index, key, pos, threading.current_thread().name)
            # sleep(0.3)
            res = download(url, f"{key}.png", os.path.join(self.CurrentDir, pos[0], pos[1]))
            if res['code'] == 0:
                model.setItem(index, 1, QStandardItem("√"))
            else:
                model.setItem(index, 1, QStandardItem(res['msg']))
            self.CurrentFinished += 1
            self.psSig.emit()


if __name__ == '__main__':
    if getattr(sys, 'frozen', None):
        basedir = sys._MEIPASS
    else:
        basedir = os.path.dirname(__file__)
    dirname = basedir
    plugin_path = os.path.join(dirname, 'platforms')
    os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = plugin_path
    print(plugin_path)

    QApplication.setStyle('Fusion')
    app = QApplication(sys.argv)
    ex = MainWindow()
    sys.exit(app.exec())
