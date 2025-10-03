"""
HearSight摘要查看器UI

显示段落划分和LLM生成的摘要
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTextEdit,
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


