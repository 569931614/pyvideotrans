"""
垂直侧边栏组件
提供现代化的功能导航界面
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel, QFrame, QScrollArea
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon, QCursor


class SidebarButton(QPushButton):
    """侧边栏按钮组件"""
    
    def __init__(self, icon, text, tooltip="", parent=None):
        super().__init__(parent)
        self.setText(f"{icon}  {text}")
        self.setToolTip(tooltip)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setFixedHeight(44)
        self.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #e8eef7;
                border: none;
                border-radius: 8px;
                padding: 12px 16px;
                text-align: left;
                font-size: 14px;
                font-weight: 500;
            }
            QPushButton:hover {
                background: rgba(99, 102, 241, 0.15);
                color: #818cf8;
            }
            QPushButton:pressed {
                background: rgba(99, 102, 241, 0.25);
            }
            QPushButton:checked {
                background: rgba(99, 102, 241, 0.2);
                color: #a5b4fc;
                border-left: 3px solid #6366f1;
            }
        """)


class SidebarSeparator(QFrame):
    """侧边栏分隔线"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.HLine)
        self.setFixedHeight(1)
        self.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.08);
                margin: 12px 16px;
            }
        """)


class SidebarSection(QWidget):
    """侧边栏分组标题"""
    
    def __init__(self, title, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 8)
        layout.setSpacing(0)
        
        label = QLabel(title)
        label.setStyleSheet("""
            QLabel {
                color: #6b7280;
                font-size: 11px;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 1.2px;
            }
        """)
        layout.addWidget(label)


class Sidebar(QWidget):
    """主侧边栏组件"""
    
    # 信号定义
    hearsight_clicked = Signal()
    config_clicked = Signal()
    summary_clicked = Signal()
    html_ui_clicked = Signal()
    qt_ui_clicked = Signal()
    settings_clicked = Signal()
    about_clicked = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        """初始化UI"""
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 创建滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:vertical {
                background: transparent;
                width: 8px;
                margin: 0;
            }
            QScrollBar::handle:vertical {
                background: rgba(255, 255, 255, 0.1);
                border-radius: 4px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(255, 255, 255, 0.15);
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)
        
        # 内容容器
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 8, 0, 8)
        content_layout.setSpacing(2)
        
        # Logo区域
        logo_section = QWidget()
        logo_layout = QVBoxLayout(logo_section)
        logo_layout.setContentsMargins(16, 20, 16, 20)

        app_name = QLabel("BDvideoTrans")
        app_name.setStyleSheet("""
            QLabel {
                color: #e8eef7;
                font-size: 18px;
                font-weight: 700;
                letter-spacing: 0.5px;
            }
        """)
        logo_layout.addWidget(app_name)
        
        app_desc = QLabel("智能视频翻译")
        app_desc.setStyleSheet("""
            QLabel {
                color: #6b7280;
                font-size: 12px;
                margin-top: 4px;
            }
        """)
        logo_layout.addWidget(app_desc)
        
        content_layout.addWidget(logo_section)
        content_layout.addWidget(SidebarSeparator())
        
        # 智能摘要组
        content_layout.addWidget(SidebarSection("智能摘要"))
        
        self.hearsight_btn = SidebarButton(
            "🎯", "HearSight",
            "基于Whisper识别结果生成智能段落划分和LLM摘要\n需要先完成语音识别并生成SRT字幕"
        )
        self.hearsight_btn.clicked.connect(self.hearsight_clicked.emit)
        content_layout.addWidget(self.hearsight_btn)
        
        self.config_btn = SidebarButton(
            "⚙️", "摘要配置",
            "配置HearSight的LLM参数、提示词等设置"
        )
        self.config_btn.clicked.connect(self.config_clicked.emit)
        content_layout.addWidget(self.config_btn)
        
        self.summary_btn = SidebarButton(
            "📚", "摘要管理",
            "查看和管理视频摘要库\n支持搜索、导出和删除"
        )
        self.summary_btn.clicked.connect(self.summary_clicked.emit)
        content_layout.addWidget(self.summary_btn)
        
        # 分隔线
        content_layout.addWidget(SidebarSeparator())
        
        # 界面切换组
        content_layout.addWidget(SidebarSection("界面"))
        
        self.html_ui_btn = SidebarButton(
            "🌐", "HTML UI",
            "切换到现代化HTML界面\n基于Web技术的全新用户体验"
        )
        self.html_ui_btn.setCheckable(True)
        self.html_ui_btn.clicked.connect(self.html_ui_clicked.emit)
        content_layout.addWidget(self.html_ui_btn)
        
        self.qt_ui_btn = SidebarButton(
            "📋", "原始界面",
            "切换回传统Qt界面"
        )
        self.qt_ui_btn.setCheckable(True)
        self.qt_ui_btn.setChecked(True)
        self.qt_ui_btn.clicked.connect(self.qt_ui_clicked.emit)
        content_layout.addWidget(self.qt_ui_btn)
        
        # 分隔线
        content_layout.addWidget(SidebarSeparator())
        
        # 工具组
        content_layout.addWidget(SidebarSection("工具"))
        
        self.settings_btn = SidebarButton(
            "⚙️", "设置",
            "应用程序设置和高级选项"
        )
        self.settings_btn.clicked.connect(self.settings_clicked.emit)
        content_layout.addWidget(self.settings_btn)
        
        self.about_btn = SidebarButton(
            "ℹ️", "关于",
            "关于BDvideoTrans"
        )
        self.about_btn.clicked.connect(self.about_clicked.emit)
        content_layout.addWidget(self.about_btn)
        
        # 底部弹簧
        content_layout.addStretch()
        
        # 版本信息
        version_label = QLabel("v3.0")
        version_label.setAlignment(Qt.AlignCenter)
        version_label.setStyleSheet("""
            QLabel {
                color: #4b5563;
                font-size: 11px;
                padding: 16px;
            }
        """)
        content_layout.addWidget(version_label)
        
        # 设置滚动区域
        scroll.setWidget(content)
        main_layout.addWidget(scroll)
        
        # 设置侧边栏样式
        self.setStyleSheet("""
            Sidebar {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #0f1419, stop:1 #0a0e13);
                border-right: 1px solid rgba(255, 255, 255, 0.08);
            }
        """)
        
        # 设置固定宽度
        self.setFixedWidth(220)
    
    def set_html_ui_checked(self, checked):
        """设置HTML UI按钮的选中状态"""
        self.html_ui_btn.setChecked(checked)
        self.qt_ui_btn.setChecked(not checked)
    
    def set_qt_ui_checked(self, checked):
        """设置Qt UI按钮的选中状态"""
        self.qt_ui_btn.setChecked(checked)
        self.html_ui_btn.setChecked(not checked)

