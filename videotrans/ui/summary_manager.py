"""
HearSight 摘要管理对话框

查看、搜索和管理已存储的视频摘要
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QSplitter,
    QPushButton, QListWidget, QListWidgetItem, QTextEdit, QTextBrowser,
    QLineEdit, QLabel, QMessageBox, QFileDialog, QComboBox, QSpinBox
)
from PySide6.QtCore import Qt, Signal, QThread, QUrl, QEvent
from PySide6.QtGui import QTextCursor, QMouseEvent
from typing import List, Dict, Any, Optional
import os
import re


class CustomTextBrowser(QTextBrowser):
    """自定义QTextBrowser，阻止默认的链接导航行为"""

    def setSource(self, url):
        """重写setSource，阻止默认的链接导航行为"""
        print(f"⚠️ CustomTextBrowser.setSource被调用: {url.toString()}")
        print(f"   不执行默认行为，保持内容不变")
        # 不调用父类的setSource，阻止默认行为
        # 这样点击链接不会尝试加载新内容
        pass

    def loadResource(self, type, url):
        """重写loadResource，阻止资源加载"""
        print(f"⚠️ CustomTextBrowser.loadResource被调用: type={type}, url={url.toString()}")
        print(f"   不加载资源，返回空")
        # 返回空，不加载任何资源
        from PySide6.QtCore import QByteArray
        return QByteArray()


class SearchThread(QThread):
    """搜索线程"""
    finished = Signal(list)
    error = Signal(str)

    def __init__(self, query: str, n_results: int = 10, parent=None):
        super().__init__(parent)
        self.query = query
        self.n_results = n_results

    def run(self):
        try:
            from videotrans.hearsight.vector_store import get_vector_store
            vector_store = get_vector_store()
            results = vector_store.search(self.query, n_results=self.n_results)
            self.finished.emit(results)
        except Exception as e:
            self.error.emit(str(e))


class SummaryManagerDialog(QDialog):
    """摘要管理对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.videos = []
        self.current_video = None
        self.current_video_path = None  # 存储当前视频路径
        self.search_thread = None

        self.setWindowTitle("HearSight - 摘要管理")
        self.resize(1400, 900)
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #0a0e27, stop:1 #121829);
            }
            QLabel {
                color: #e8eef7;
            }
        """)

        self.init_ui()
        self.load_videos()

    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # 标题区域
        title_layout = QHBoxLayout()
        title_label = QLabel("  📚  视频摘要库")
        title_label.setStyleSheet("""
            font-size: 22px;
            font-weight: bold;
            padding: 14px 20px;
            color: #a78bfa;
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #1a1f3a, stop:1 #151a30);
            border-radius: 12px;
            border: 2px solid #2a3244;
        """)
        title_layout.addWidget(title_label)

        # 刷新按钮
        self.refresh_btn = QPushButton("🔄 刷新")
        self.refresh_btn.setFixedSize(110, 44)
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #6c757d, stop:1 #5a6268);
                color: white;
                border: 2px solid #3f4b63;
                border-radius: 10px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #7a8290, stop:1 #6a7280);
                border-color: #4f5b73;
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #5a6268, stop:1 #4a5258);
            }
        """)
        self.refresh_btn.clicked.connect(self.load_videos)
        title_layout.addWidget(self.refresh_btn)

        layout.addLayout(title_layout)

        # 搜索区域
        search_layout = QHBoxLayout()
        search_label = QLabel("🔍 语义搜索:")
        search_label.setStyleSheet("""
            font-size: 15px;
            font-weight: bold;
            color: #a0abc0;
            padding: 5px;
        """)
        search_layout.addWidget(search_label)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("输入关键词进行语义搜索...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                border: 2px solid #2a3244;
                border-radius: 8px;
                padding: 12px 16px;
                background-color: #121829;
                color: #e8eef7;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #6366f1;
                background-color: #1a1f3a;
            }
            QLineEdit::placeholder {
                color: #6b7280;
            }
        """)
        self.search_input.returnPressed.connect(self.perform_search)
        search_layout.addWidget(self.search_input)

        search_label2 = QLabel("结果数:")
        search_layout.addWidget(search_label2)

        self.results_count = QSpinBox()
        self.results_count.setRange(1, 50)
        self.results_count.setValue(10)
        self.results_count.setFixedWidth(90)
        self.results_count.setStyleSheet("""
            QSpinBox {
                border: 2px solid #2a3244;
                border-radius: 8px;
                padding: 10px;
                background-color: #121829;
                color: #e8eef7;
                font-size: 14px;
            }
            QSpinBox:focus {
                border-color: #6366f1;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                background-color: #1a1f3a;
                border: 1px solid #2a3244;
            }
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {
                background-color: #2a3244;
            }
        """)
        search_layout.addWidget(self.results_count)

        self.search_btn = QPushButton("搜索")
        self.search_btn.setFixedSize(110, 44)
        self.search_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #6366f1, stop:1 #4f46e5);
                color: white;
                border: 2px solid #4f46e5;
                border-radius: 10px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #7c7ff5, stop:1 #6366f1);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #4f46e5, stop:1 #4338ca);
            }
        """)
        self.search_btn.clicked.connect(self.perform_search)
        search_layout.addWidget(self.search_btn)

        self.clear_search_btn = QPushButton("清除")
        self.clear_search_btn.setFixedSize(90, 44)
        self.clear_search_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #6c757d, stop:1 #5a6268);
                color: white;
                border: 2px solid #3f4b63;
                border-radius: 10px;
                font-size: 14px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #7a8290, stop:1 #6a7280);
                border-color: #4f5b73;
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #5a6268, stop:1 #4a5258);
            }
        """)
        self.clear_search_btn.clicked.connect(self.clear_search)
        search_layout.addWidget(self.clear_search_btn)

        layout.addLayout(search_layout)

        # 主内容区域（三栏布局）
        splitter = QSplitter(Qt.Horizontal)

        # 左侧：视频列表
        left_panel = self.create_video_list_panel()
        splitter.addWidget(left_panel)

        # 右侧：摘要详情
        right_panel = self.create_detail_panel()
        splitter.addWidget(right_panel)

        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)

        layout.addWidget(splitter)

        # 底部按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.export_btn = QPushButton("📥 导出Markdown")
        self.export_btn.setEnabled(False)
        self.export_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #10b981, stop:1 #059669);
                color: white;
                border: 2px solid #059669;
                padding: 14px 32px;
                border-radius: 10px;
                font-size: 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #34d399, stop:1 #10b981);
            }
            QPushButton:disabled {
                background: #2a3244;
                color: #6b7280;
                border-color: #2a3244;
            }
        """)
        self.export_btn.clicked.connect(self.export_current)
        button_layout.addWidget(self.export_btn)

        self.delete_btn = QPushButton("🗑️ 删除")
        self.delete_btn.setEnabled(False)
        self.delete_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ef4444, stop:1 #dc2626);
                color: white;
                border: 2px solid #dc2626;
                padding: 14px 32px;
                border-radius: 10px;
                font-size: 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f87171, stop:1 #ef4444);
            }
            QPushButton:disabled {
                background: #2a3244;
                color: #6b7280;
                border-color: #2a3244;
            }
        """)
        self.delete_btn.clicked.connect(self.delete_current)
        button_layout.addWidget(self.delete_btn)

        self.close_btn = QPushButton("关闭")
        self.close_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #6c757d, stop:1 #5a6268);
                color: white;
                border: 2px solid #3f4b63;
                padding: 14px 32px;
                border-radius: 10px;
                font-size: 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #7a8290, stop:1 #6a7280);
                border-color: #4f5b73;
            }
        """)
        self.close_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.close_btn)

        layout.addLayout(button_layout)

    def create_video_list_panel(self):
        """创建视频列表面板"""
        from PySide6.QtWidgets import QWidget

        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)

        # 标题
        label = QLabel("  📹  视频列表")
        label.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            padding: 12px 16px;
            color: #e8eef7;
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #1a1f3a, stop:1 #151a30);
            border: 2px solid #2a3244;
            border-radius: 12px 12px 0 0;
        """)
        layout.addWidget(label)

        # 视频列表
        self.video_list = QListWidget()
        self.video_list.setStyleSheet("""
            QListWidget {
                border: 2px solid #2a3244;
                border-top: none;
                border-radius: 0 0 12px 12px;
                background-color: #121829;
                outline: none;
            }
            QListWidget::item {
                padding: 16px 14px;
                border-bottom: 1px solid #1a1f3a;
                color: #a0abc0;
                font-size: 14px;
            }
            QListWidget::item:selected {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #6366f1, stop:1 #4f46e5);
                color: white;
                font-weight: bold;
                border-radius: 8px;
                border: none;
            }
            QListWidget::item:hover:!selected {
                background-color: #1a1f3a;
                border-radius: 8px;
            }
        """)
        self.video_list.itemClicked.connect(self.on_video_selected)
        layout.addWidget(self.video_list)

        # 统计信息
        self.stats_label = QLabel("总计: 0 个视频")
        self.stats_label.setStyleSheet("""
            font-size: 13px;
            color: #6b7280;
            padding: 10px 14px;
            background-color: #0a0e27;
            border: 2px solid #2a3244;
            border-top: none;
            border-radius: 0 0 12px 12px;
        """)
        layout.addWidget(self.stats_label)

        return panel

    def create_detail_panel(self):
        """创建详情面板"""
        from PySide6.QtWidgets import QWidget, QTabWidget

        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)

        # 使用 Tab 切换不同视图
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 2px solid #2a3244;
                border-radius: 12px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1a1f3a, stop:1 #151a30);
            }
            QTabBar::tab {
                background: #121829;
                color: #a0abc0;
                padding: 12px 24px;
                margin-right: 6px;
                border: 2px solid #2a3244;
                border-bottom: none;
                border-radius: 10px 10px 0 0;
                font-weight: bold;
                font-size: 14px;
            }
            QTabBar::tab:selected {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1a1f3a, stop:1 #151a30);
                color: #6366f1;
                border-color: #2a3244;
            }
            QTabBar::tab:hover:!selected {
                background: #1a1f3a;
                color: #e8eef7;
            }
        """)

        # Tab 1: 整体摘要
        self.summary_tab = QTextEdit()
        self.summary_tab.setReadOnly(True)
        self.summary_tab.setStyleSheet("""
            QTextEdit {
                background-color: #121829;
                color: #e8eef7;
                border: none;
                padding: 24px;
                font-size: 15px;
                line-height: 2.0;
            }
        """)
        self.tab_widget.addTab(self.summary_tab, "📋 整体摘要")

        # Tab 2: 段落列表
        # 使用QTextEdit而不是QTextBrowser，避免链接处理问题
        self.paragraph_tab = QTextEdit()
        self.paragraph_tab.setReadOnly(True)
        # QTextEdit不支持anchorClicked，需要使用其他方式处理链接点击
        # 我们将使用鼠标点击事件来处理
        self.paragraph_tab.viewport().installEventFilter(self)
        self.paragraph_tab.setStyleSheet("""
            QTextBrowser {
                background-color: #121829;
                color: #e8eef7;
                border: none;
                padding: 24px;
                font-size: 14px;
                line-height: 1.9;
            }
        """)
        self.tab_widget.addTab(self.paragraph_tab, "📝 段落详情")

        # Tab 3: 搜索结果
        self.search_results_tab = QTextEdit()
        self.search_results_tab.setReadOnly(True)
        self.search_results_tab.setStyleSheet("""
            QTextEdit {
                background-color: #121829;
                color: #e8eef7;
                border: none;
                padding: 24px;
                font-size: 14px;
                line-height: 1.9;
            }
        """)
        self.tab_widget.addTab(self.search_results_tab, "🔍 搜索结果")

        layout.addWidget(self.tab_widget)

        return panel

    def load_videos(self):
        """加载视频列表"""
        import traceback
        print(f"\n📋 load_videos() 被调用")
        print(f"   调用堆栈:")
        for line in traceback.format_stack()[:-1]:
            print(f"   {line.strip()}")

        try:
            from videotrans.hearsight.vector_store import get_vector_store
            vector_store = get_vector_store()
            self.videos = vector_store.list_all_videos()

            self.video_list.clear()
            for video in self.videos:
                topic = video.get('topic', '无主题')
                para_count = video.get('paragraph_count', 0)
                duration = video.get('total_duration', 0)
                video_path = video.get('video_path', '')

                # 格式化时长
                duration_str = f"{int(duration//60)}:{int(duration%60):02d}"

                # 创建列表项
                item_text = f"🎬 {topic}\n   📊 {para_count}段 | ⏱ {duration_str}"
                item = QListWidgetItem(item_text)
                item.setData(Qt.UserRole, video)
                self.video_list.addItem(item)

            # 更新统计
            self.stats_label.setText(f"总计: {len(self.videos)} 个视频")

            # 清空详情
            print(f"⚠️ 清空段落详情（load_videos）")
            self.summary_tab.clear()
            self.paragraph_tab.clear()
            self.current_video = None
            self.export_btn.setEnabled(False)
            self.delete_btn.setEnabled(False)

        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载视频列表失败：\n{str(e)}")

    def on_video_selected(self, item: QListWidgetItem):
        """视频被选中"""
        video = item.data(Qt.UserRole)
        self.current_video = video
        self.current_video_path = video['video_path']  # 保存视频路径
        self.load_video_detail(video['video_path'])

        # 启用按钮
        self.export_btn.setEnabled(True)
        self.delete_btn.setEnabled(True)

        # 切换到摘要 Tab
        self.tab_widget.setCurrentIndex(0)

    def load_video_detail(self, video_path: str):
        """加载视频详情"""
        try:
            from videotrans.hearsight.vector_store import get_vector_store
            vector_store = get_vector_store()
            summary_data = vector_store.get_video_summary(video_path)

            if not summary_data:
                QMessageBox.warning(self, "提示", "未找到该视频的摘要数据")
                return

            # 显示整体摘要
            overall_meta = summary_data['overall']['metadata']
            topic = overall_meta.get('topic', '无主题')
            para_count = overall_meta.get('paragraph_count', 0)
            duration = overall_meta.get('total_duration', 0)
            duration_str = f"{int(duration//60)}:{int(duration%60):02d}"

            # 从文档中提取摘要文本
            doc = summary_data['overall']['document']
            summary_text = doc.split('总结: ')[-1] if '总结: ' in doc else doc

            summary_html = f"""
            <div style="font-family: 'Microsoft YaHei', Arial, sans-serif;">
                <h1 style="color: #a78bfa; margin: 0 0 20px 0; font-size: 26px; font-weight: bold;">
                    {topic}
                </h1>
                <div style="background: linear-gradient(135deg, #1a1f3a 0%, #151a30 100%);
                            padding: 24px;
                            border-radius: 12px;
                            margin-bottom: 24px;
                            border-left: 5px solid #6366f1;">
                    <p style="margin: 0; line-height: 2.0; color: #e8eef7; font-size: 16px;">
                        {summary_text}
                    </p>
                </div>
                <div style="padding: 18px;
                            background: linear-gradient(135deg, #121829 0%, #0a0e27 100%);
                            border-radius: 10px;
                            border: 2px solid #2a3244;">
                    <span style="color: #a0abc0; font-size: 15px;">
                        <b style="color: #6366f1;">📊 段落数</b>: {para_count} &nbsp;&nbsp;|&nbsp;&nbsp;
                        <b style="color: #6366f1;">⏱ 总时长</b>: {duration_str} &nbsp;&nbsp;|&nbsp;&nbsp;
                        <b style="color: #6366f1;">📁 文件</b>: {os.path.basename(video_path)}
                    </span>
                </div>
            </div>
            """
            self.summary_tab.setHtml(summary_html)

            # 显示段落列表
            paragraphs_html = """
            <div style="font-family: 'Microsoft YaHei', Arial, sans-serif;">
                <h2 style="color: #a78bfa; margin: 0 0 18px 0; font-size: 22px; font-weight: bold;">段落详情</h2>
            """

            for i, para in enumerate(summary_data['paragraphs'], 1):
                meta = para['metadata']
                start = meta.get('start_time', 0)
                end = meta.get('end_time', 0)
                start_str = f"{int(start//60):02d}:{int(start%60):02d}"
                end_str = f"{int(end//60):02d}:{int(end%60):02d}"

                # 提取段落摘要和完整文本
                doc = para['document']
                if '段落摘要: ' in doc and '\n完整内容: ' in doc:
                    parts = doc.split('\n完整内容: ')
                    para_summary = parts[0].replace('段落摘要: ', '').strip()
                    para_text = parts[1].strip() if len(parts) > 1 else ''
                else:
                    para_summary = meta.get('paragraph_summary', '')
                    para_text = doc

                # 创建可点击的时间链接
                # 注意：不能使用 playvideo://0.0 因为QUrl会将其解析为IP地址
                # 使用路径格式：playvideo:///时间戳
                time_link = f"playvideo:///{start}"

                paragraphs_html += f"""
                <div style="background: linear-gradient(135deg, #121829 0%, #0a0e27 100%);
                            padding: 18px;
                            border-radius: 10px;
                            margin-bottom: 18px;
                            border: 2px solid #2a3244;
                            border-left: 4px solid #6366f1;">
                    <div style="margin-bottom: 12px;">
                        <span style="color: #a78bfa; font-weight: bold; font-size: 15px;">
                            📍 段落 {i}
                        </span>
                        <a href="{time_link}" style="color: #60a5fa; font-size: 14px; margin-left: 12px;
                           text-decoration: none; cursor: pointer; padding: 4px 10px;
                           background: rgba(96, 165, 250, 0.1); border-radius: 6px;
                           border: 1px solid rgba(96, 165, 250, 0.3);">
                            ▶️ {start_str} - {end_str}
                        </a>
                    </div>
                """

                if para_summary:
                    paragraphs_html += f"""
                    <div style="background: linear-gradient(135deg, #2a2210 0%, #1f1a08 100%);
                                padding: 14px;
                                border-radius: 8px;
                                margin-bottom: 12px;
                                border-left: 3px solid #f59e0b;
                                border: 2px solid #3d2f15;">
                        <div style="color: #fbbf24; font-weight: bold; font-size: 14px; margin-bottom: 6px;">
                            💡 摘要
                        </div>
                        <div style="color: #fde68a; font-size: 14px; line-height: 1.8;">
                            {para_summary}
                        </div>
                    </div>
                    """

                if para_text:
                    text_html = para_text.replace('\n', '<br>')
                    paragraphs_html += f"""
                    <div style="color: #a0abc0; font-size: 14px; line-height: 1.9;">
                        {text_html}
                    </div>
                    """

                paragraphs_html += "</div>"

            paragraphs_html += "</div>"
            print(f"📝 设置段落HTML内容，长度: {len(paragraphs_html)}")
            self.paragraph_tab.setHtml(paragraphs_html)
            print(f"📝 设置后段落详情内容长度: {len(self.paragraph_tab.toPlainText())}")

        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载视频详情失败：\n{str(e)}")

    def perform_search(self):
        """执行搜索"""
        query = self.search_input.text().strip()
        if not query:
            QMessageBox.warning(self, "提示", "请输入搜索关键词")
            return

        # 切换到搜索结果 Tab
        self.tab_widget.setCurrentIndex(2)
        self.search_results_tab.setHtml("<p>搜索中...</p>")

        # 启动搜索线程
        if self.search_thread and self.search_thread.isRunning():
            self.search_thread.terminate()
            self.search_thread.wait()

        n_results = self.results_count.value()
        self.search_thread = SearchThread(query, n_results, self)
        self.search_thread.finished.connect(self.on_search_finished)
        self.search_thread.error.connect(self.on_search_error)
        self.search_thread.start()

    def on_search_finished(self, results: List[Dict[str, Any]]):
        """搜索完成"""
        if not results:
            self.search_results_tab.setHtml("<p>未找到相关结果</p>")
            return

        # 显示搜索结果
        results_html = f"""
        <div style="font-family: 'Microsoft YaHei', Arial, sans-serif;">
            <h2 style="color: #a78bfa; margin: 0 0 18px 0; font-size: 22px; font-weight: bold;">
                搜索结果 ({len(results)} 条)
            </h2>
        """

        for i, result in enumerate(results, 1):
            meta = result['metadata']
            doc = result['document']
            distance = result.get('distance', 0)

            # 相似度（距离越小越相似）
            similarity = (1 - distance) * 100

            video_path = meta.get('video_path', '')
            video_name = os.path.basename(video_path)

            # 提取内容
            if meta.get('type') == 'overall_summary':
                content_type = "📋 整体摘要"
                time_info = ""
            else:
                content_type = "📝 段落内容"
                start = meta.get('start_time', 0)
                end = meta.get('end_time', 0)
                start_str = f"{int(start//60):02d}:{int(start%60):02d}"
                end_str = f"{int(end//60):02d}:{int(end%60):02d}"
                time_info = f"<br><span style='color: #6b7280; font-size: 13px;'>⏱ {start_str} - {end_str}</span>"

            # 处理文本
            display_text = doc[:200] + "..." if len(doc) > 200 else doc
            display_text = display_text.replace('\n', '<br>')

            # 动态选择边框和背景颜色
            if similarity > 80:
                border_color = '#10b981'
                badge_bg = '#064e3b'
                badge_text = '#6ee7b7'
            elif similarity > 60:
                border_color = '#6366f1'
                badge_bg = '#1e1b4b'
                badge_text = '#a5b4fc'
            else:
                border_color = '#f59e0b'
                badge_bg = '#451a03'
                badge_text = '#fcd34d'

            results_html += f"""
            <div style="background: linear-gradient(135deg, #121829 0%, #0a0e27 100%);
                        padding: 18px;
                        border-radius: 10px;
                        margin-bottom: 18px;
                        border: 2px solid #2a3244;
                        border-left: 4px solid {border_color};">
                <div style="margin-bottom: 10px;">
                    <span style="background-color: {badge_bg};
                                color: {badge_text};
                                padding: 4px 10px;
                                border-radius: 6px;
                                font-size: 12px;
                                font-weight: bold;">
                        相似度: {similarity:.1f}%
                    </span>
                    <span style="margin-left: 12px; color: #6b7280; font-size: 14px;">
                        {content_type}
                    </span>
                </div>
                <div style="color: #a78bfa; font-weight: bold; font-size: 15px; margin-bottom: 8px;">
                    🎬 {video_name}
                    {time_info}
                </div>
                <div style="color: #a0abc0; font-size: 14px; line-height: 1.8;">
                    {display_text}
                </div>
            </div>
            """

        results_html += "</div>"
        self.search_results_tab.setHtml(results_html)

    def on_search_error(self, error_msg: str):
        """搜索出错"""
        QMessageBox.critical(self, "搜索错误", f"搜索失败：\n{error_msg}")
        self.search_results_tab.setHtml(f"<p style='color: red;'>搜索失败: {error_msg}</p>")

    def clear_search(self):
        """清除搜索"""
        self.search_input.clear()
        self.search_results_tab.clear()
        self.tab_widget.setCurrentIndex(0)

    def export_current(self):
        """导出当前视频摘要"""
        if not self.current_video:
            return

        video_path = self.current_video['video_path']

        # 选择保存路径
        default_name = f"{self.current_video.get('topic', 'summary')}_摘要.md"
        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "导出摘要",
            default_name,
            "Markdown files (*.md);;All files (*.*)"
        )

        if not save_path:
            return

        try:
            from videotrans.hearsight.vector_store import get_vector_store
            vector_store = get_vector_store()
            summary_data = vector_store.get_video_summary(video_path)

            if not summary_data:
                QMessageBox.warning(self, "提示", "未找到摘要数据")
                return

            # 构建 Markdown 内容
            overall_meta = summary_data['overall']['metadata']
            topic = overall_meta.get('topic', '无主题')
            para_count = overall_meta.get('paragraph_count', 0)
            duration = overall_meta.get('total_duration', 0)
            duration_str = f"{int(duration//60)}:{int(duration%60):02d}"

            doc = summary_data['overall']['document']
            summary_text = doc.split('总结: ')[-1] if '总结: ' in doc else doc

            with open(save_path, 'w', encoding='utf-8') as f:
                f.write(f"# {topic}\n\n")
                f.write(f"## 总结\n\n")
                f.write(f"{summary_text}\n\n")
                f.write(f"**段落数**: {para_count} | **总时长**: {duration_str}\n\n")
                f.write(f"**视频文件**: `{os.path.basename(video_path)}`\n\n")
                f.write(f"---\n\n")
                f.write(f"## 详细内容\n\n")

                for i, para in enumerate(summary_data['paragraphs'], 1):
                    meta = para['metadata']
                    start = meta.get('start_time', 0)
                    end = meta.get('end_time', 0)
                    start_str = f"{int(start//60):02d}:{int(start%60):02d}"
                    end_str = f"{int(end//60):02d}:{int(end%60):02d}"

                    f.write(f"### 段落 {i}: [{start_str} - {end_str}]\n\n")

                    # 提取段落摘要和文本
                    doc = para['document']
                    if '段落摘要: ' in doc and '\n完整内容: ' in doc:
                        parts = doc.split('\n完整内容: ')
                        para_summary = parts[0].replace('段落摘要: ', '').strip()
                        para_text = parts[1].strip() if len(parts) > 1 else ''

                        if para_summary:
                            f.write(f"**摘要**: {para_summary}\n\n")
                        if para_text:
                            f.write(f"{para_text}\n\n")
                    else:
                        f.write(f"{doc}\n\n")

            QMessageBox.information(self, "成功", f"摘要已导出到:\n{save_path}")

        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出失败：\n{str(e)}")

    def delete_current(self):
        """删除当前视频摘要"""
        if not self.current_video:
            return

        video_path = self.current_video['video_path']
        topic = self.current_video.get('topic', '该视频')

        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定要删除 [{topic}] 的摘要数据吗？\n\n此操作不可恢复！",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                from videotrans.hearsight.vector_store import get_vector_store
                vector_store = get_vector_store()
                success = vector_store.delete_video(video_path)

                if success:
                    QMessageBox.information(self, "成功", "摘要已删除")
                    self.load_videos()
                else:
                    QMessageBox.warning(self, "提示", "未找到该视频的摘要数据")

            except Exception as e:
                QMessageBox.critical(self, "错误", f"删除失败：\n{str(e)}")

    def eventFilter(self, obj, event):
        """事件过滤器，处理段落详情中的链接点击"""
        if obj == self.paragraph_tab.viewport() and event.type() == QEvent.MouseButtonPress:
            # 获取点击位置的光标
            cursor = self.paragraph_tab.cursorForPosition(event.pos())
            # 获取光标处的字符格式
            char_format = cursor.charFormat()
            # 检查是否是链接
            if char_format.isAnchor():
                anchor_href = char_format.anchorHref()
                print(f"\n🔗 检测到链接点击: {anchor_href}")
                # 创建QUrl对象
                url = QUrl(anchor_href)
                self.on_time_link_clicked(url)
                return True  # 事件已处理

        return super().eventFilter(obj, event)

    def on_time_link_clicked(self, url: QUrl):
        """处理时间链接点击"""
        print(f"\n🔗 链接被点击")
        print(f"   URL: {url.toString()}")
        print(f"   当前段落详情内容长度: {len(self.paragraph_tab.toPlainText())}")

        # 检查是否是播放视频的链接
        if url.scheme() == "playvideo":
            try:
                # 从URL路径中提取时间戳
                # URL格式: playvideo:///时间戳
                time_str = url.path().strip('/')

                # 调试信息
                print(f"🔍 Debug: URL scheme = {url.scheme()}")
                print(f"🔍 Debug: URL path = {url.path()}")
                print(f"🔍 Debug: time_str = '{time_str}'")

                # 尝试转换为浮点数
                try:
                    start_time = float(time_str)
                except ValueError as ve:
                    QMessageBox.critical(
                        self,
                        "时间格式错误",
                        f"无法解析时间戳：'{time_str}'\n\n"
                        f"URL: {url.toString()}\n\n"
                        f"错误: {str(ve)}"
                    )
                    return

                # 检查视频文件是否存在
                if not self.current_video_path or not os.path.exists(self.current_video_path):
                    QMessageBox.warning(
                        self,
                        "视频不存在",
                        f"视频文件不存在或已被移动：\n{self.current_video_path}"
                    )
                    return

                # 播放视频并跳转到指定时间
                print(f"📝 播放前段落详情内容长度: {len(self.paragraph_tab.toPlainText())}")
                self.play_video_at_time(self.current_video_path, start_time)
                print(f"📝 播放后段落详情内容长度: {len(self.paragraph_tab.toPlainText())}")

            except Exception as e:
                import traceback
                error_detail = traceback.format_exc()
                print(f"❌ 异常后段落详情内容长度: {len(self.paragraph_tab.toPlainText())}")
                QMessageBox.critical(
                    self,
                    "错误",
                    f"播放视频失败：\n{str(e)}\n\n详细信息:\n{error_detail}"
                )

    def find_target_video(self, source_video_path: str) -> str:
        """
        查找翻译后的目标视频

        Args:
            source_video_path: 原始视频路径

        Returns:
            目标视频路径，如果找不到则返回原始路径
        """
        print(f"\n🔍 开始查找目标视频...")
        print(f"   原始路径: {source_video_path}")

        # 检查原始视频是否存在
        if not os.path.exists(source_video_path):
            print(f"   ⚠️ 原始视频不存在！")
            return source_video_path

        # 获取视频目录和文件名
        video_dir = os.path.dirname(source_video_path)
        video_basename = os.path.splitext(os.path.basename(source_video_path))[0]
        video_ext = os.path.splitext(source_video_path)[1]

        print(f"   目录: {video_dir}")
        print(f"   文件名: {video_basename}")
        print(f"   扩展名: {video_ext}")

        # 常见的目标视频命名模式
        target_patterns = [
            f"{video_basename}_target{video_ext}",  # 原名_target.mp4
            f"{video_basename}-target{video_ext}",  # 原名-target.mp4
            f"{video_basename}.target{video_ext}",  # 原名.target.mp4
            f"{video_basename}_translated{video_ext}",  # 原名_translated.mp4
            f"{video_basename}-translated{video_ext}",  # 原名-translated.mp4
        ]

        # 查找目标视频
        print(f"   查找目标视频...")
        for i, pattern in enumerate(target_patterns, 1):
            target_path = os.path.join(video_dir, pattern)
            print(f"   [{i}] 检查: {os.path.basename(target_path)}")
            if os.path.exists(target_path):
                print(f"   ✅ 找到目标视频: {target_path}")
                return target_path
            else:
                print(f"       不存在")

        # 如果找不到，返回原始视频
        print(f"   ⚠️ 未找到目标视频，使用原始视频: {source_video_path}")
        return source_video_path

    def play_video_at_time(self, video_path: str, start_time: float):
        """
        播放视频并跳转到指定时间（使用内嵌播放器）

        Args:
            video_path: 视频文件路径
            start_time: 开始时间（秒）
        """
        try:
            print(f"\n▶️ 准备播放视频...")
            print(f"   视频路径: {video_path}")
            print(f"   开始时间: {start_time}秒")

            # 查找翻译后的目标视频
            target_video = self.find_target_video(video_path)

            print(f"\n🎬 打开播放器...")
            print(f"   最终视频: {target_video}")
            print(f"   跳转时间: {start_time}秒")

            # 使用内嵌播放器（非模态）
            from videotrans.ui.video_player import VideoPlayerDialog

            # 创建播放器并保存引用，防止被垃圾回收
            player = VideoPlayerDialog(target_video, start_time, self)

            # 使用show()而不是exec()，避免阻塞父窗口
            player.show()

            # 保存播放器引用，防止被垃圾回收
            if not hasattr(self, '_video_players'):
                self._video_players = []
            self._video_players.append(player)

            # 当播放器关闭时，从列表中移除
            player.finished.connect(lambda: self._video_players.remove(player) if player in self._video_players else None)

        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            print(f"\n❌ 播放失败: {e}")
            print(error_detail)
            QMessageBox.critical(
                self,
                "播放失败",
                f"无法播放视频：\n{str(e)}\n\n详细信息:\n{error_detail}"
            )


