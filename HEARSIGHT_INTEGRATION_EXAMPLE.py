"""
HearSight功能集成到主窗口的示例代码

将以下代码集成到 videotrans/mainwin/_main_win.py 的 MainWindow 类中
"""

# ====== 在 MainWindow 类的 __init__ 方法末尾添加 ======
def init_hearsight(self):
    """初始化HearSight功能"""
    # 加载HearSight配置
    self.hearsight_config = self._load_hearsight_config()

    # 初始化处理器
    self.hearsight_processor = None


# ====== 在 MainWindow 类的 initUI 方法中添加按钮 ======
def add_hearsight_button(self):
    """在主界面添加HearSight按钮"""
    # 方案1：添加到工具栏
    self.hearsight_btn = QPushButton("🎯 智能摘要")
    self.hearsight_btn.setToolTip(
        "基于Whisper识别结果生成智能段落划分和LLM摘要\n"
        "需要先完成语音识别并生成SRT字幕"
    )
    self.hearsight_btn.setStyleSheet("""
        QPushButton {
            background-color: #28a745;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            font-size: 13px;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #218838;
        }
        QPushButton:pressed {
            background-color: #1e7e34;
        }
    """)
    self.hearsight_btn.clicked.connect(self.open_hearsight)

    # 添加到状态栏或工具栏
    if hasattr(self, 'toolBar'):
        self.toolBar.addSeparator()
        self.toolBar.addWidget(self.hearsight_btn)

    # 方案2：添加配置按钮
    self.hearsight_config_btn = QPushButton("⚙️")
    self.hearsight_config_btn.setToolTip("HearSight配置")
    self.hearsight_config_btn.setFixedSize(32, 32)
    self.hearsight_config_btn.clicked.connect(self.open_hearsight_config)
    if hasattr(self, 'toolBar'):
        self.toolBar.addWidget(self.hearsight_config_btn)


# ====== 添加HearSight相关方法 ======
def _load_hearsight_config(self):
    """加载HearSight配置"""
    import json
    from videotrans.configure import config

    # 尝试从文件加载
    config_path = os.path.join(config.ROOT_DIR, 'hearsight_config.json')
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"加载HearSight配置失败: {e}")

    # 返回默认配置
    return {
        'llm': {
            'api_key': '',
            'base_url': 'https://api.openai.com/v1',
            'model': 'gpt-3.5-turbo',
            'temperature': 0.3,
            'timeout': 120
        },
        'merge': {
            'max_gap': 2.0,
            'max_duration': 30.0,
            'max_chars': 200
        }
    }


def open_hearsight_config(self):
    """打开HearSight配置对话框"""
    from videotrans.ui.hearsight_config import HearSightConfigDialog
    from PySide6.QtWidgets import QMessageBox

    try:
        dialog = HearSightConfigDialog(self)
        dialog.config_saved.connect(self._on_hearsight_config_saved)
        dialog.exec()
    except Exception as e:
        QMessageBox.critical(self, "错误", f"打开配置对话框失败：\n{str(e)}")


def _on_hearsight_config_saved(self):
    """配置保存后的回调"""
    # 重新加载配置
    self.hearsight_config = self._load_hearsight_config()
    from PySide6.QtWidgets import QMessageBox
    QMessageBox.information(self, "提示", "配置已更新")


def open_hearsight(self):
    """打开HearSight功能"""
    from PySide6.QtWidgets import QMessageBox, QFileDialog, QProgressDialog
    from videotrans.ui.hearsight_viewer import SummaryViewerDialog
    from videotrans.hearsight.processor import HearSightProcessor
    from videotrans.configure import config

    try:
        # 检查配置
        llm_config = self.hearsight_config.get('llm', {})
        if not llm_config.get('api_key'):
            reply = QMessageBox.question(
                self,
                "配置提示",
                "尚未配置LLM API密钥，是否现在配置？",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.open_hearsight_config()
            return

        # 选择SRT文件
        srt_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择SRT字幕文件",
            config.params.get('target_dir', ''),
            "SRT Files (*.srt);;All Files (*)"
        )

        if not srt_path:
            return

        # 创建进度对话框
        progress = QProgressDialog("正在处理...", "取消", 0, 100, self)
        progress.setWindowModality(Qt.WindowModal)
        progress.setWindowTitle("HearSight处理中")
        progress.setMinimumDuration(0)
        progress.setValue(0)

        # 创建处理器
        self.hearsight_processor = HearSightProcessor(
            srt_path=srt_path,
            llm_config=self.hearsight_config['llm'],
            merge_config=self.hearsight_config['merge']
        )

        # 连接信号
        self.hearsight_processor.progress_updated.connect(
            lambda text, percent: self._update_hearsight_progress(progress, text, percent)
        )

        self.hearsight_processor.finished.connect(
            lambda summary, paragraphs: self._show_hearsight_result(progress, summary, paragraphs)
        )

        self.hearsight_processor.error_occurred.connect(
            lambda error: self._handle_hearsight_error(progress, error)
        )

        # 开始处理
        self.hearsight_processor.start()

    except Exception as e:
        QMessageBox.critical(self, "错误", f"启动HearSight处理失败：\n{str(e)}")


def _update_hearsight_progress(self, progress_dialog, text, percent):
    """更新进度"""
    progress_dialog.setLabelText(text)
    progress_dialog.setValue(percent)


def _show_hearsight_result(self, progress_dialog, summary, paragraphs):
    """显示处理结果"""
    from videotrans.ui.hearsight_viewer import SummaryViewerDialog
    from PySide6.QtWidgets import QMessageBox

    try:
        progress_dialog.close()

        # 显示结果对话框
        viewer = SummaryViewerDialog(self)
        viewer.set_data(summary, paragraphs)
        viewer.exec()

    except Exception as e:
        QMessageBox.critical(self, "错误", f"显示结果失败：\n{str(e)}")


def _handle_hearsight_error(self, progress_dialog, error):
    """处理错误"""
    from PySide6.QtWidgets import QMessageBox

    progress_dialog.close()
    QMessageBox.critical(
        self,
        "HearSight处理失败",
        f"处理过程中发生错误：\n\n{error}\n\n"
        "请检查：\n"
        "1. SRT文件格式是否正确\n"
        "2. LLM API配置是否正确\n"
        "3. 网络连接是否正常"
    )


# ====== 集成说明 ======
"""
将以上方法添加到 MainWindow 类中，然后在 __init__ 方法末尾调用：

def __init__(self, parent=None, width=1200, height=650):
    # ... 现有代码 ...

    # 初始化HearSight
    self.init_hearsight()

    # 在initUI完成后添加HearSight按钮
    QTimer.singleShot(900, self.add_hearsight_button)
"""


# ====== 使用流程说明 ======
"""
用户使用流程：

1. 配置HearSight
   - 点击工具栏的 "⚙️" 按钮
   - 填写LLM API配置（API Key、Base URL、Model等）
   - 调整段落合并参数
   - 测试连接并保存

2. 处理视频
   方案A - 使用已有SRT：
   - 点击 "🎯 智能摘要" 按钮
   - 选择已生成的SRT文件
   - 等待处理完成
   - 查看段落和摘要结果

   方案B - 自动集成到视频处理流程：
   - 在视频翻译完成后自动提示
   - 询问是否生成智能摘要
   - 自动使用生成的SRT文件

3. 查看和导出
   - 浏览段落列表
   - 点击段落查看详细内容
   - 导出为Markdown文件
"""
