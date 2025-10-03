import requests
from PySide6 import QtCore, QtWidgets
from PySide6.QtCore import QByteArray, QThread, Signal
from PySide6.QtGui import Qt, QPixmap

from videotrans.configure import config
from videotrans.util import tools


class Ui_infoform(object):
    def setupUi(self, infoform):
        infoform.setObjectName("infoform")
        infoform.setWindowModality(QtCore.Qt.NonModal)
        infoform.resize(950, 600)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(infoform.sizePolicy().hasHeightForWidth())
        infoform.setSizePolicy(sizePolicy)
        self.v1 = QtWidgets.QVBoxLayout(infoform)
        # 将 v1 设为垂直顶部对齐
        self.v1.setAlignment(Qt.AlignTop)

        self.label = QtWidgets.QLabel(infoform)
        self.label.setText(
            '关于 translateVideo' if config.defaulelang == 'zh' else 'About translateVideo')
        self.label.setStyleSheet("""font-size:20px""")
        self.v1.addWidget(self.label)

        self.text1 = QtWidgets.QPlainTextEdit(infoform)
        self.text1.setObjectName("text1")
        self.text1.setReadOnly(True)
        self.text1.setMaximumHeight(180)
        self.text1.setPlainText("""本项目为免费工具，欢迎学习和使用。"""
                                if config.defaulelang == 'zh' else
                                """This is a free tool for video translation and dubbing.""")
        # text1的边框合为0
        self.text1.setFrameStyle(QtWidgets.QFrame.NoFrame)
        self.text1.setStyleSheet("""
        border:none;
        """)
        self.v1.addWidget(self.text1)

        self.link = QtWidgets.QPushButton(infoform)
        self.link.setText(
            " 感谢使用 translateVideo " if config.defaulelang == 'zh' else " Thanks for using translateVideo ")
        # 设置高度35px，最大宽度300
        self.link.setFixedHeight(35)
        self.link.setStyleSheet("""background-color:transparent""")
        self.link.setCursor(Qt.PointingHandCursor)
        self.link.clicked.connect(lambda: tools.open_url('about:blank'))

        # donation UI removed

        # donation QR and external link removed
        # disclaimer button removed
        self.v1.addStretch()
        infoform.setWindowTitle(
            "关于 translateVideo" if config.defaulelang == 'zh' else "About translateVideo")
        QtCore.QMetaObject.connectSlotsByName(infoform)

    def showimg(self, name):
        pixmap = QPixmap()
        pixmap.loadFromData(config.INFO_WIN['data'][name])
        pixmap = pixmap.scaledToHeight(200, Qt.SmoothTransformation)
        if name == 'wxpay':
            self.wxpay.setPixmap(pixmap)
        elif name == 'alipay':
            self.alipay.setPixmap(pixmap)
        elif name == 'mp':
            self.mp.setPixmap(pixmap)

    # 重写关闭事件，当关闭时仅隐藏
    def closeEvent(self, event):
        self.hide()


class DownloadImg(QThread):
    finished = Signal(str)

    def __init__(self, parent=None, urls=None):
        super().__init__(parent=parent)
        self.urls = urls

    def run(self):
        """下载网络图片并返回图片数据"""
        # 遍历字典 self.urls 分别获取 key和value
        try:
            response = requests.get(self.urls['link'])
            if response.status_code == 200:
                config.INFO_WIN["data"][self.urls['name']] = QByteArray(response.content)
                self.finished.emit(self.urls['name'])
        except:
            pass
