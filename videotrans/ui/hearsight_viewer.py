"""
HearSight摘要查看器UI

显示段落划分和LLM生成的摘要
"""
from PySide6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QTextEdit,
    QPushButton, QLabel, QSplitter, QListWidget,
    QListWidgetItem, QMessageBox, QFileDialog
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from typing import List, Dict, Any
import os


class SummaryViewerDialog(QDialog):
    """摘要查看器对话框"""

    def __init__(self, parent=None, video_path=None):
        super().__init__(parent)
        self.paragraphs = []
        self.summary = {}
        self.video_path = video_path  # 存储视频路径

        self.setWindowTitle("HearSight - 智能摘要")
        self.resize(1200, 800)
        self.setStyleSheet("""
            QDialog {
                background-color: #f5f7fa;
            }
            QLabel {
                color: #2c3e50;
            }
        """)

        self.init_ui()

    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)

        # 顶部：总摘要区域
        summary_label = QLabel("  📝  内容摘要")
        summary_label.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            padding: 12px 15px;
            color: #2c3e50;
            background-color: white;
            border-radius: 8px 8px 0 0;
        """)
        layout.addWidget(summary_label)

        self.summary_text = QTextEdit()
        self.summary_text.setReadOnly(True)
        self.summary_text.setMaximumHeight(150)
        self.summary_text.setStyleSheet("""
            QTextEdit {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ffffff, stop:1 #f0f8ff);
                border: 2px solid #d6e9f5;
                border-radius: 0 0 10px 10px;
                padding: 18px;
                font-size: 14px;
                line-height: 1.6;
            }
        """)
        layout.addWidget(self.summary_text)

        # 中部：段落列表和内容（分栏布局）
        splitter = QSplitter(Qt.Horizontal)

        # 左侧：段落列表
        left_widget = QVBoxLayout()
        para_label = QLabel("  📑  段落列表")
        para_label.setStyleSheet("""
            font-size: 15px;
            font-weight: bold;
            padding: 10px 12px;
            color: #2c3e50;
            background-color: white;
            border-radius: 8px 8px 0 0;
        """)

        self.paragraph_list = QListWidget()
        self.paragraph_list.setStyleSheet("""
            QListWidget {
                border: 2px solid #e8ecef;
                border-radius: 0 0 10px 10px;
                background-color: white;
                outline: none;
            }
            QListWidget::item {
                padding: 14px 12px;
                border-bottom: 1px solid #f0f3f5;
                color: #495057;
                font-size: 13px;
                cursor: pointer;
            }
            QListWidget::item:selected {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4a9eff, stop:1 #357abd);
                color: white;
                font-weight: bold;
                border-radius: 6px;
                border: none;
            }
            QListWidget::item:hover:!selected {
                background-color: #e8f4fd;
                border-radius: 6px;
            }
        """)
        self.paragraph_list.itemClicked.connect(self.on_paragraph_selected)
        self.paragraph_list.itemDoubleClicked.connect(self.on_paragraph_double_clicked)

        left_container = QVBoxLayout()
        left_container.addWidget(para_label)
        left_container.addWidget(self.paragraph_list)

        from PySide6.QtWidgets import QWidget
        left_panel = QWidget()
        left_panel.setLayout(left_container)
        left_panel.setMinimumWidth(200)

        # 右侧：段落详细内容
        right_widget = QVBoxLayout()
        content_label = QLabel("  📄  段落内容")
        content_label.setStyleSheet("""
            font-size: 15px;
            font-weight: bold;
            padding: 10px 12px;
            color: #2c3e50;
            background-color: white;
            border-radius: 8px 8px 0 0;
        """)

        self.content_text = QTextEdit()
        self.content_text.setReadOnly(True)
        self.content_text.setStyleSheet("""
            QTextEdit {
                border: 2px solid #e8ecef;
                border-radius: 0 0 10px 10px;
                padding: 18px;
                font-size: 14px;
                line-height: 1.8;
                background-color: white;
            }
        """)

        right_container = QVBoxLayout()
        right_container.addWidget(content_label)
        right_container.addWidget(self.content_text)

        right_panel = QWidget()
        right_panel.setLayout(right_container)

        # 添加到分栏
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 1)  # 左侧占1份
        splitter.setStretchFactor(1, 2)  # 右侧占2份

        layout.addWidget(splitter, 1)  # 拉伸因子为1，占据剩余空间

        # 底部：按钮区域
        button_layout = QHBoxLayout()

        self.export_btn = QPushButton("导出Markdown")
        self.export_btn.clicked.connect(self.export_markdown)
        self.export_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #5aa9ff, stop:1 #4a9eff);
                color: white;
                border: none;
                padding: 12px 28px;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #6ab9ff, stop:1 #5aa9ff);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3a8eef, stop:1 #2a7edf);
            }
        """)

        self.close_btn = QPushButton("关闭")
        self.close_btn.clicked.connect(self.accept)
        self.close_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #7c8a99, stop:1 #6c757d);
                color: white;
                border: none;
                padding: 12px 28px;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #8a98a7, stop:1 #7a8290);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #5a6268, stop:1 #4a5258);
            }
        """)

        button_layout.addStretch()
        button_layout.addWidget(self.export_btn)
        button_layout.addWidget(self.close_btn)

        layout.addLayout(button_layout)

    def set_data(self, summary: Dict[str, Any], paragraphs: List[Dict[str, Any]]):
        """
        设置数据

        Args:
            summary: 总摘要数据
            paragraphs: 段落列表
        """
        self.summary = summary
        self.paragraphs = paragraphs

        # 显示总摘要
        topic = summary.get("topic", "")
        summary_text = summary.get("summary", "")
        para_count = summary.get("paragraph_count", len(paragraphs))
        duration = summary.get("total_duration", 0.0)

        duration_str = f"{int(duration//60)}:{int(duration%60):02d}"

        summary_html = f"""
        <div style="font-family: 'Microsoft YaHei', Arial, sans-serif;">
            <h2 style="color: #2c5aa0; margin: 0 0 16px 0; font-size: 20px; font-weight: bold;">
                {topic if topic else '视频内容摘要'}
            </h2>
            <p style="margin: 0 0 16px 0; line-height: 1.8; color: #34495e; font-size: 14px;">
                {summary_text}
            </p>
            <div style="padding: 12px; background-color: #f8f9fa; border-radius: 6px; border-left: 4px solid #4a9eff;">
                <span style="color: #495057; font-size: 13px;">
                    <b style="color: #2c5aa0;">📊 段落数</b>: {para_count} &nbsp;&nbsp;|&nbsp;&nbsp;
                    <b style="color: #2c5aa0;">⏱ 总时长</b>: {duration_str}
                </span>
            </div>
        </div>
        """

        self.summary_text.setHtml(summary_html)

        # 填充段落列表
        self.paragraph_list.clear()
        for para in paragraphs:
            start = para.get("start_time", 0.0)
            end = para.get("end_time", 0.0)
            text = para.get("text", "")
            summary = para.get("summary", "").strip()

            # 格式化时间
            start_str = f"{int(start//60):02d}:{int(start%60):02d}"
            end_str = f"{int(end//60):02d}:{int(end%60):02d}"

            # 创建列表项 - 如果有摘要则显示摘要，否则显示原文预览
            if summary:
                # 有摘要：显示时间范围 + 摘要预览
                preview = summary[:40] + "..." if len(summary) > 40 else summary
                item_text = f"[{start_str}-{end_str}] 💡 {preview}"
            else:
                # 无摘要：显示时间范围 + 原文预览
                preview = text[:30] + "..." if len(text) > 30 else text
                item_text = f"[{start_str}-{end_str}] {preview}"

            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, para)  # 存储完整段落数据
            self.paragraph_list.addItem(item)

        # 默认选中第一个段落
        if paragraphs:
            self.paragraph_list.setCurrentRow(0)
            self.on_paragraph_selected(self.paragraph_list.item(0))

    def on_paragraph_selected(self, item: QListWidgetItem):
        """段落被选中时的处理"""
        para = item.data(Qt.UserRole)
        if not para:
            return

        start = para.get("start_time", 0.0)
        end = para.get("end_time", 0.0)
        text = para.get("text", "")

        start_str = f"{int(start//60):02d}:{int(start%60):02d}"
        end_str = f"{int(end//60):02d}:{int(end%60):02d}"

        # 处理换行符（f-string中不能包含反斜杠）
        text_html = text.replace('\n', '<br>')

        # 获取段落摘要（如果存在）
        para_summary = para.get('summary', '').strip()

        # 构建HTML内容
        content_html = f"""
        <div style="font-family: 'Microsoft YaHei', Arial, sans-serif;">
            <div style="background: linear-gradient(135deg, #e8f4f8 0%, #d6e9f5 100%);
                        padding: 16px 20px;
                        border-radius: 10px;
                        margin-bottom: 20px;
                        border-left: 5px solid #4a9eff;
                        box-shadow: 0 2px 8px rgba(74, 158, 255, 0.1);">
                <span style="color: #2c5aa0; font-weight: bold; font-size: 15px;">⏱ 时间段:</span>
                <span style="color: #2c3e50; font-size: 15px; font-weight: 600; margin-left: 8px;">
                    {start_str} - {end_str}
                </span>
            </div>
            {f'''<div style="background: linear-gradient(135deg, #fff9e6 0%, #fff3d9 100%);
                        padding: 14px 18px;
                        border-radius: 8px;
                        margin-bottom: 18px;
                        border-left: 4px solid #ffb833;
                        box-shadow: 0 2px 6px rgba(255, 184, 51, 0.15);">
                <div style="color: #856404; font-weight: bold; font-size: 14px; margin-bottom: 6px;">
                    💡 段落摘要
                </div>
                <div style="color: #664d03; font-size: 13px; line-height: 1.7;">
                    {para_summary}
                </div>
            </div>''' if para_summary else ''}
            <div style="line-height: 2.0; color: #34495e; font-size: 14px; padding: 0 8px;">
                {text_html}
            </div>
        </div>
        """

        self.content_text.setHtml(content_html)

    def export_markdown(self):
        """导出为Markdown文件"""
        if not self.paragraphs:
            QMessageBox.warning(self, "提示", "没有可导出的内容")
            return

        # 选择保存路径
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "导出Markdown",
            "",
            "Markdown Files (*.md);;All Files (*)"
        )

        if not file_path:
            return

        try:
            # 导出
            from videotrans.hearsight.summarizer import export_summary_to_markdown
            export_summary_to_markdown(
                self.summary,
                self.paragraphs,
                file_path
            )

            QMessageBox.information(self, "成功", f"已导出到：\n{file_path}")

        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出失败：\n{str(e)}")

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

        # 1. 首先检查标准的翻译输出位置
        # 格式：原始目录/_video_out/视频名/视频名.mp4
        standard_target_dir = os.path.join(video_dir, "_video_out", video_basename)
        standard_target_path = os.path.join(standard_target_dir, f"{video_basename}{video_ext}")

        print(f"\n   [标准位置] 检查翻译输出目录:")
        print(f"   {standard_target_path}")
        if os.path.exists(standard_target_path):
            print(f"   ✅ 找到翻译后的视频（标准位置）: {standard_target_path}")
            return standard_target_path
        else:
            print(f"   ⚠️ 标准位置不存在")

        # 2. 检查同目录下的常见命名模式
        target_patterns = [
            f"{video_basename}_target{video_ext}",  # 原名_target.mp4
            f"{video_basename}-target{video_ext}",  # 原名-target.mp4
            f"{video_basename}.target{video_ext}",  # 原名.target.mp4
            f"{video_basename}_translated{video_ext}",  # 原名_translated.mp4
            f"{video_basename}-translated{video_ext}",  # 原名-translated.mp4
        ]

        print(f"\n   [同目录] 查找其他命名模式...")
        for i, pattern in enumerate(target_patterns, 1):
            target_path = os.path.join(video_dir, pattern)
            print(f"   [{i}] 检查: {os.path.basename(target_path)}")
            if os.path.exists(target_path):
                print(f"   ✅ 找到目标视频（同目录）: {target_path}")
                return target_path
            else:
                print(f"       不存在")

        # 如果找不到，返回原始视频
        print(f"\n   ⚠️ 未找到翻译后的视频，使用原始视频: {source_video_path}")
        return source_video_path

    def on_paragraph_double_clicked(self, item: QListWidgetItem):
        """双击段落时播放视频"""
        para = item.data(Qt.UserRole)
        if not para:
            return

        # 检查是否有视频路径
        if not self.video_path:
            QMessageBox.warning(self, "提示", "未设置视频路径，无法播放")
            return

        # 检查视频文件是否存在
        if not os.path.exists(self.video_path):
            QMessageBox.warning(
                self,
                "视频不存在",
                f"视频文件不存在或已被移动：\n{self.video_path}"
            )
            return

        # 获取开始时间
        start_time = para.get("start_time", 0.0)

        try:
            print(f"\n▶️ 准备播放视频...")
            print(f"   视频路径: {self.video_path}")
            print(f"   开始时间: {start_time}秒")

            # 查找翻译后的目标视频
            target_video = self.find_target_video(self.video_path)

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


class SummaryViewerWidget(QWidget):
    """摘要查看器Widget - 用于嵌入主窗口"""

    def __init__(self, parent=None, video_path=None):
        super().__init__(parent)
        self.paragraphs = []
        self.summary = {}
        self.video_path = video_path

        self.setStyleSheet("""
            QWidget {
                background-color: #f5f7fa;
            }
            QLabel {
                color: #2c3e50;
            }
        """)

        self.init_ui()

    def init_ui(self):
        """初始化UI - 复用Dialog的布局"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        # 顶部工具栏
        toolbar = QHBoxLayout()

        title_label = QLabel("📝 智能摘要")
        title_label.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #E6E8EB;
            padding: 10px 15px;
            background-color: #2A2F3A;
            border-radius: 8px;
        """)
        toolbar.addWidget(title_label)
        toolbar.addStretch()

        # 返回按钮
        back_btn = QPushButton("← 返回主界面")
        back_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #6c757d, stop:1 #5a6268);
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-size: 13px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #7c8a99, stop:1 #6c757d);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #5a6268, stop:1 #4a5258);
            }
        """)
        back_btn.clicked.connect(self.return_to_main)
        toolbar.addWidget(back_btn)

        layout.addLayout(toolbar)

        # 总摘要区域
        summary_label = QLabel("  📝  内容摘要")
        summary_label.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            padding: 12px 15px;
            color: #E6E8EB;
            background-color: #2A2F3A;
            border-radius: 8px 8px 0 0;
        """)
        layout.addWidget(summary_label)

        self.summary_text = QTextEdit()
        self.summary_text.setReadOnly(True)
        self.summary_text.setMaximumHeight(150)
        self.summary_text.setStyleSheet("""
            QTextEdit {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2A2F3A, stop:1 #1F2430);
                border: 2px solid #3A4250;
                border-radius: 0 0 10px 10px;
                padding: 18px;
                font-size: 14px;
                line-height: 1.6;
                color: #E6E8EB;
            }
        """)
        layout.addWidget(self.summary_text)

        # 段落列表和内容（分栏布局）
        splitter = QSplitter(Qt.Horizontal)

        # 左侧：段落列表
        from PySide6.QtWidgets import QWidget as QW
        left_container = QW()
        left_layout = QVBoxLayout(left_container)
        left_layout.setContentsMargins(0, 0, 0, 0)

        para_label = QLabel("  📑  段落列表")
        para_label.setStyleSheet("""
            font-size: 15px;
            font-weight: bold;
            padding: 10px 12px;
            color: #E6E8EB;
            background-color: #2A2F3A;
            border-radius: 8px 8px 0 0;
        """)
        left_layout.addWidget(para_label)

        self.paragraph_list = QListWidget()
        self.paragraph_list.setStyleSheet("""
            QListWidget {
                border: 2px solid #3A4250;
                border-radius: 0 0 10px 10px;
                background-color: #1F2430;
                outline: none;
            }
            QListWidget::item {
                padding: 14px 12px;
                border-bottom: 1px solid #2A2F3A;
                color: #E6E8EB;
                font-size: 13px;
            }
            QListWidget::item:hover {
                background-color: #2A3F5F;
            }
            QListWidget::item:selected {
                background-color: #4A6FA5;
                color: white;
            }
        """)
        self.paragraph_list.currentRowChanged.connect(self.on_paragraph_selected)
        left_layout.addWidget(self.paragraph_list)

        splitter.addWidget(left_container)

        # 右侧：段落详情
        right_container = QW()
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(0, 0, 0, 0)

        detail_label = QLabel("  📄  段落详情")
        detail_label.setStyleSheet("""
            font-size: 15px;
            font-weight: bold;
            padding: 10px 12px;
            color: #E6E8EB;
            background-color: #2A2F3A;
            border-radius: 8px 8px 0 0;
        """)
        right_layout.addWidget(detail_label)

        self.detail_text = QTextEdit()
        self.detail_text.setReadOnly(True)
        self.detail_text.setStyleSheet("""
            QTextEdit {
                border: 2px solid #3A4250;
                border-radius: 0 0 10px 10px;
                background-color: #1F2430;
                padding: 15px;
                font-size: 13px;
                line-height: 1.8;
                color: #E6E8EB;
            }
        """)
        right_layout.addWidget(self.detail_text)

        splitter.addWidget(right_container)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)

        layout.addWidget(splitter)

        # 底部按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        export_btn = QPushButton("💾 导出摘要")
        export_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #34ce57, stop:1 #28a745);
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-size: 14px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #40d967, stop:1 #2dbd4e);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #218838, stop:1 #1e7e34);
            }
        """)
        export_btn.clicked.connect(self.export_summary)
        button_layout.addWidget(export_btn)

        layout.addLayout(button_layout)

    def set_data(self, summary: Dict[str, Any], paragraphs: List[Dict[str, Any]]):
        """设置数据"""
        self.summary = summary
        self.paragraphs = paragraphs

        # 显示总摘要
        summary_html = f"""
        <div style="line-height: 1.8; color: #E6E8EB;">
            <p style="margin: 0 0 10px 0;"><strong>📊 总时长：</strong>{summary.get('total_duration', 'N/A')}</p>
            <p style="margin: 0 0 10px 0;"><strong>📝 段落数：</strong>{summary.get('paragraph_count', 0)}</p>
            <p style="margin: 10px 0;"><strong>💡 内容概要：</strong></p>
            <p style="margin: 0; color: #A0ABC0;">{summary.get('overall_summary', '暂无摘要')}</p>
        </div>
        """
        self.summary_text.setHtml(summary_html)

        # 填充段落列表
        self.paragraph_list.clear()
        for i, para in enumerate(paragraphs, 1):
            item_text = f"段落 {i}  |  {para.get('start_time', '')} - {para.get('end_time', '')}"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, para)
            self.paragraph_list.addItem(item)

        # 默认选中第一个
        if paragraphs:
            self.paragraph_list.setCurrentRow(0)

    def set_video_path(self, video_path):
        """设置视频路径"""
        self.video_path = video_path

    def on_paragraph_selected(self, index):
        """段落选中事件"""
        if index < 0 or index >= len(self.paragraphs):
            return

        para = self.paragraphs[index]

        # 构建详情HTML
        detail_html = f"""
        <div style="line-height: 2.0; color: #E6E8EB;">
            <h3 style="color: #6AB9FF; margin-top: 0;">段落 {index + 1}</h3>
            <p><strong>⏱️ 时间范围：</strong>{para.get('start_time', '')} - {para.get('end_time', '')}</p>
            <p><strong>⏳ 时长：</strong>{para.get('duration', 'N/A')}</p>

            <h4 style="color: #FFA726; margin-top: 20px;">📝 段落摘要</h4>
            <p style="background-color: #2A2F3A; padding: 12px; border-left: 4px solid #FFA726; border-radius: 4px; color: #E6E8EB;">
                {para.get('summary', '暂无摘要')}
            </p>

            <h4 style="color: #66BB6A; margin-top: 20px;">📄 原文内容</h4>
            <div style="background-color: #2A2F3A; padding: 12px; border-left: 4px solid #66BB6A; border-radius: 4px; color: #A0ABC0;">
                {para.get('text', '').replace(chr(10), '<br>')}
            </div>
        </div>
        """

        self.detail_text.setHtml(detail_html)

    def export_summary(self):
        """导出摘要"""
        if not self.summary or not self.paragraphs:
            QMessageBox.warning(self, "警告", "没有可导出的摘要数据")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "导出摘要",
            "",
            "Markdown Files (*.md);;Text Files (*.txt);;All Files (*)"
        )

        if not file_path:
            return

        try:
            content = self._generate_export_content()

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

            QMessageBox.information(self, "成功", f"摘要已导出到：\n{file_path}")

        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出失败：\n{str(e)}")

    def _generate_export_content(self) -> str:
        """生成导出内容"""
        lines = []
        lines.append("# HearSight 智能摘要\n")
        lines.append(f"**总时长：** {self.summary.get('total_duration', 'N/A')}\n")
        lines.append(f"**段落数：** {self.summary.get('paragraph_count', 0)}\n")
        lines.append(f"\n## 内容概要\n")
        lines.append(f"{self.summary.get('overall_summary', '暂无摘要')}\n")
        lines.append(f"\n## 段落详情\n")

        for i, para in enumerate(self.paragraphs, 1):
            lines.append(f"\n### 段落 {i}\n")
            lines.append(f"**时间：** {para.get('start_time', '')} - {para.get('end_time', '')}\n")
            lines.append(f"**时长：** {para.get('duration', 'N/A')}\n")
            lines.append(f"\n**摘要：**\n{para.get('summary', '暂无摘要')}\n")
            lines.append(f"\n**原文：**\n```\n{para.get('text', '')}\n```\n")

        return "\n".join(lines)

    def return_to_main(self):
        """返回主界面"""
        # 获取主窗口（需要向上查找，因为直接父对象可能是 QStackedWidget）
        from PySide6.QtWidgets import QMainWindow

        main_window = None
        parent = self.parent()

        # 向上查找主窗口
        while parent:
            if isinstance(parent, QMainWindow):
                main_window = parent
                break
            parent = parent.parent()

        if not main_window:
            return

        # 现在使用主窗口的 _central_stack
        if hasattr(main_window, '_central_stack') and main_window._central_stack:
            # 检查是否启用了 HTML UI
            if hasattr(main_window, 'html_view') and main_window.html_view is not None:
                # 如果 HTML UI 存在，切换到 HTML UI
                html_index = main_window._central_stack.indexOf(main_window.html_view)
                if html_index >= 0:
                    main_window._central_stack.setCurrentIndex(html_index)
                else:
                    # HTML UI 不在 stack 中，切换到第一个（Qt UI）
                    main_window._central_stack.setCurrentIndex(0)
            else:
                # 没有 HTML UI，切换到第一个widget（Qt UI）
                main_window._central_stack.setCurrentIndex(0)

