"""
HearSight配置对话框

配置LLM API参数
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QComboBox, QPushButton, QLabel,
    QGroupBox, QSpinBox, QDoubleSpinBox, QMessageBox,
    QScrollArea, QWidget, QTextEdit
)
from PySide6.QtCore import Qt, Signal, QThread
from videotrans.configure import config
import json


class ConnectionTestThread(QThread):
    """后台测试连接线程"""
    finished = Signal(bool, str)  # success, message

    def __init__(self, api_key, base_url, model, test_vector=False,
                 volc_api_key=None, volc_base_url=None, volc_model=None):
        super().__init__()
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.test_vector = test_vector
        self.volc_api_key = volc_api_key
        self.volc_base_url = volc_base_url
        self.volc_model = volc_model

    def run(self):
        try:
            # 测试LLM连接
            from videotrans.hearsight.chat_client import chat_simple

            response = chat_simple(
                prompt="请用一句话回复：你好",
                api_key=self.api_key,
                base_url=self.base_url,
                model=self.model,
                timeout=30
            )

            llm_result = f"[OK] LLM连接正常\n\n模型响应：{response[:100]}"

            # 测试向量化服务
            if self.test_vector:
                if not self.volc_api_key or not self.volc_base_url or not self.volc_model:
                    self.finished.emit(False, "[错误] 火山引擎向量化配置不完整")
                    return

                from videotrans.hearsight.volcengine_vector import VolcengineVectorClient

                volc_client = VolcengineVectorClient(
                    api_key=self.volc_api_key,
                    base_url=self.volc_base_url,
                    embedding_model=self.volc_model
                )

                if volc_client.test_connection():
                    vector_result = "\n\n[OK] 火山引擎向量化服务连接正常"
                else:
                    vector_result = "\n\n[失败] 火山引擎向量化服务连接失败"

                llm_result += vector_result

            self.finished.emit(True, llm_result)

        except Exception as e:
            self.finished.emit(False, f"连接测试失败：\n{str(e)}")


class HearSightConfigDialog(QDialog):
    """HearSight配置对话框"""

    config_saved = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        # 保存测试线程引用
        self.test_thread = None

        self.setWindowTitle("[配置] 智能摘要配置")
        self.resize(950, 800)
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f0f4f8, stop:1 #e8eef5);
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #d0dae6;
                border-radius: 12px;
                margin-top: 16px;
                padding-top: 24px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ffffff, stop:1 #f8fbff);
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 20px;
                padding: 0 10px;
                color: #2d3748;
                background-color: white;
                font-size: 15px;
                font-weight: 600;
            }
            QLabel {
                color: #2d3748;
                font-size: 13px;
                font-weight: 500;
                background-color: transparent;
            }
            QLineEdit {
                border: 2px solid #cbd5e0;
                border-radius: 8px;
                padding: 11px 14px;
                background-color: white;
                font-size: 13px;
                color: #2d3748;
                selection-background-color: #4a9eff;
            }
            QLineEdit:focus {
                border-color: #4a9eff;
                background-color: #f7fafc;
                box-shadow: 0 0 0 3px rgba(74, 158, 255, 0.1);
            }
            QLineEdit:hover {
                border-color: #a0aec0;
            }
            QComboBox {
                border: 2px solid #cbd5e0;
                border-radius: 8px;
                padding: 9px 12px;
                background-color: white;
                font-size: 13px;
                color: #2d3748;
                min-height: 20px;
            }
            QComboBox:focus {
                border-color: #4a9eff;
                background-color: #f7fafc;
                box-shadow: 0 0 0 3px rgba(74, 158, 255, 0.1);
            }
            QComboBox:hover {
                border-color: #a0aec0;
            }
            QComboBox::drop-down {
                border: none;
                width: 30px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid #718096;
                margin-right: 8px;
            }
            QDoubleSpinBox, QSpinBox {
                border: 2px solid #cbd5e0;
                border-radius: 8px;
                padding: 9px 12px;
                background-color: white;
                font-size: 13px;
                color: #2d3748;
                min-height: 20px;
            }
            QDoubleSpinBox:focus, QSpinBox:focus {
                border-color: #4a9eff;
                background-color: #f7fafc;
                box-shadow: 0 0 0 3px rgba(74, 158, 255, 0.1);
            }
            QDoubleSpinBox:hover, QSpinBox:hover {
                border-color: #a0aec0;
            }
            QDoubleSpinBox::up-button, QSpinBox::up-button,
            QDoubleSpinBox::down-button, QSpinBox::down-button {
                border: none;
                background: transparent;
                width: 20px;
            }
            QDoubleSpinBox::up-button:hover, QSpinBox::up-button:hover,
            QDoubleSpinBox::down-button:hover, QSpinBox::down-button:hover {
                background: #e2e8f0;
            }
        """)

        self.init_ui()
        self.load_config()

    def init_ui(self):
        """初始化UI"""
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # 顶部标题（固定不滚动）
        title_label = QLabel("[配置] 智能摘要配置中心")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 20px;
                font-weight: bold;
                color: #1a365d;
                background-color: #f0f4f8;
                padding: 20px 30px;
            }
        """)
        main_layout.addWidget(title_label)

        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QScrollArea.NoFrame)
        scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: transparent;
                border: none;
            }
            QScrollBar:vertical {
                border: none;
                background: #f0f4f8;
                width: 12px;
                margin: 0;
            }
            QScrollBar::handle:vertical {
                background: #cbd5e0;
                border-radius: 6px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background: #a0aec0;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)

        # 滚动内容容器
        scroll_content = QWidget()
        layout = QVBoxLayout(scroll_content)
        layout.setSpacing(24)
        layout.setContentsMargins(30, 20, 30, 30)

        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area)

        # LLM API配置组
        llm_group = QGroupBox("  🤖  LLM API 配置")
        llm_layout = QFormLayout()
        llm_layout.setSpacing(16)
        llm_layout.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        llm_layout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)

        # API Key
        api_key_label = QLabel("🔑 API Key *:")
        api_key_label.setStyleSheet("QLabel { color: #2d3748; background-color: transparent; }")
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.Password)
        self.api_key_input.setPlaceholderText("输入你的API密钥（必填）")
        self.api_key_input.setMinimumWidth(350)
        llm_layout.addRow(api_key_label, self.api_key_input)

        # Base URL
        base_url_label = QLabel("🌐 Base URL *:")
        base_url_label.setStyleSheet("QLabel { color: #2d3748; background-color: transparent; }")
        self.base_url_input = QLineEdit()
        self.base_url_input.setPlaceholderText("例如: https://api.openai.com/v1")
        self.base_url_input.setText("https://api.openai.com/v1")
        self.base_url_input.setMinimumWidth(350)
        llm_layout.addRow(base_url_label, self.base_url_input)

        # Model
        model_label = QLabel("🤖 Model *:")
        model_label.setStyleSheet("QLabel { color: #2d3748; background-color: transparent; }")
        self.model_combo = QComboBox()
        self.model_combo.setEditable(True)
        self.model_combo.addItems([
            "gpt-3.5-turbo",
            "gpt-4",
            "gpt-4-turbo",
            "gpt-4o",
            "deepseek-chat",
            "gemini-pro",
            "claude-3-sonnet",
        ])
        self.model_combo.setMinimumWidth(350)
        llm_layout.addRow(model_label, self.model_combo)

        # Temperature
        temp_label = QLabel("🌡️ Temperature:")
        temp_label.setStyleSheet("QLabel { color: #2d3748; background-color: transparent; }")
        self.temperature_spin = QDoubleSpinBox()
        self.temperature_spin.setRange(0.0, 2.0)
        self.temperature_spin.setSingleStep(0.1)
        self.temperature_spin.setValue(0.3)
        self.temperature_spin.setDecimals(1)
        self.temperature_spin.setMinimumWidth(150)
        llm_layout.addRow(temp_label, self.temperature_spin)

        # Timeout
        timeout_label = QLabel("⏱️ 超时时间:")
        timeout_label.setStyleSheet("QLabel { color: #2d3748; background-color: transparent; }")
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(10, 300)
        self.timeout_spin.setSingleStep(10)
        self.timeout_spin.setValue(120)
        self.timeout_spin.setSuffix(" 秒")
        self.timeout_spin.setMinimumWidth(150)
        llm_layout.addRow(timeout_label, self.timeout_spin)

        llm_group.setLayout(llm_layout)
        layout.addWidget(llm_group)

        # 段落合并配置组
        merge_group = QGroupBox("  📐  段落合并参数")
        merge_layout = QFormLayout()
        merge_layout.setSpacing(16)
        merge_layout.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        merge_layout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)

        # 最大时间间隔
        max_gap_label = QLabel("⏳ 最大时间间隔:")
        max_gap_label.setStyleSheet("QLabel { color: #2d3748; background-color: transparent; }")
        self.max_gap_spin = QDoubleSpinBox()
        self.max_gap_spin.setRange(0.5, 10.0)
        self.max_gap_spin.setSingleStep(0.5)
        self.max_gap_spin.setValue(2.0)
        self.max_gap_spin.setDecimals(1)
        self.max_gap_spin.setSuffix(" 秒")
        self.max_gap_spin.setMinimumWidth(150)
        merge_layout.addRow(max_gap_label, self.max_gap_spin)

        # 最大段落时长
        max_duration_label = QLabel("⏱️ 最大段落时长:")
        max_duration_label.setStyleSheet("QLabel { color: #2d3748; background-color: transparent; }")
        self.max_duration_spin = QDoubleSpinBox()
        self.max_duration_spin.setRange(10.0, 120.0)
        self.max_duration_spin.setSingleStep(5.0)
        self.max_duration_spin.setValue(30.0)
        self.max_duration_spin.setDecimals(0)
        self.max_duration_spin.setSuffix(" 秒")
        self.max_duration_spin.setMinimumWidth(150)
        merge_layout.addRow(max_duration_label, self.max_duration_spin)

        # 最大字符数
        max_chars_label = QLabel("📝 最大字符数:")
        max_chars_label.setStyleSheet("QLabel { color: #2d3748; background-color: transparent; }")
        self.max_chars_spin = QSpinBox()
        self.max_chars_spin.setRange(50, 1000)
        self.max_chars_spin.setSingleStep(50)
        self.max_chars_spin.setValue(200)
        self.max_chars_spin.setMinimumWidth(150)
        merge_layout.addRow(max_chars_label, self.max_chars_spin)

        merge_group.setLayout(merge_layout)
        layout.addWidget(merge_group)

        # 提示词配置组 ⭐ NEW
        prompt_group = QGroupBox("  📝  提示词配置")
        prompt_layout = QFormLayout()
        prompt_layout.setSpacing(16)
        prompt_layout.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        prompt_layout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)

        # 段落摘要提示词
        para_prompt_label = QLabel("📄 段落摘要提示词:")
        para_prompt_label.setStyleSheet("QLabel { color: #2d3748; background-color: transparent; }")
        self.para_prompt_input = QTextEdit()
        # 设置默认提示词
        default_para_prompt = """请用一句话（不超过50字）总结以下内容的核心要点：

{text}

只输出总结内容，不要有任何前缀或后缀。"""
        self.para_prompt_input.setPlainText(default_para_prompt)
        self.para_prompt_input.setMaximumHeight(120)
        self.para_prompt_input.setMinimumWidth(450)
        prompt_layout.addRow(para_prompt_label, self.para_prompt_input)

        # 整体摘要提示词
        overall_prompt_label = QLabel("📋 整体摘要提示词:")
        overall_prompt_label.setStyleSheet("QLabel { color: #2d3748; background-color: transparent; }")
        self.overall_prompt_input = QTextEdit()
        # 设置默认提示词
        default_overall_prompt = """你是一个专业的内容总结助手。请基于以下带时间戳的段落内容，生成一个简洁准确的中文摘要。

要求：
1. 提炼内容的核心主题（topic）和关键信息
2. 生成一段简明的中文总结（summary），涵盖主要信息点
3. 避免流水账和冗余重复
4. 总结要准确反映原文内容，不要添加原文没有的信息
5. 输出格式必须是一个JSON对象，包含topic和summary两个字段

输出格式示例：
{"topic": "主题描述", "summary": "详细总结内容"}

下面是带时间戳的段落内容：

{paragraphs}

请生成JSON格式的摘要（只输出JSON，不要包含任何其他文本）："""
        self.overall_prompt_input.setPlainText(default_overall_prompt)
        self.overall_prompt_input.setMaximumHeight(180)
        self.overall_prompt_input.setMinimumWidth(450)
        prompt_layout.addRow(overall_prompt_label, self.overall_prompt_input)

        prompt_group.setLayout(prompt_layout)
        layout.addWidget(prompt_group)

        # 向量化服务配置组
        vector_group = QGroupBox("  🗄️  向量化服务配置")
        vector_layout = QFormLayout()
        vector_layout.setSpacing(16)
        vector_layout.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        vector_layout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)

        # 向量存储类型
        vector_type_label = QLabel("📦 向量存储类型:")
        vector_type_label.setStyleSheet("QLabel { color: #2d3748; background-color: transparent; }")
        self.vector_type_combo = QComboBox()
        self.vector_type_combo.addItems([
            "ChromaDB (本地)",
            "火山引擎向量化服务"
        ])
        self.vector_type_combo.setMinimumWidth(350)
        self.vector_type_combo.currentIndexChanged.connect(self._on_vector_type_changed)
        vector_layout.addRow(vector_type_label, self.vector_type_combo)

        # 火山引擎配置容器
        self.volcengine_widget = QGroupBox()
        volcengine_layout = QFormLayout()
        volcengine_layout.setSpacing(12)
        volcengine_layout.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # API Key
        volc_api_key_label = QLabel("🔑 API Key:")
        volc_api_key_label.setStyleSheet("QLabel { color: #2d3748; background-color: transparent; }")
        self.volc_api_key_input = QLineEdit()
        self.volc_api_key_input.setEchoMode(QLineEdit.Password)
        self.volc_api_key_input.setPlaceholderText("输入火山引擎API密钥")
        self.volc_api_key_input.setMinimumWidth(350)
        volcengine_layout.addRow(volc_api_key_label, self.volc_api_key_input)

        # Base URL
        volc_base_url_label = QLabel("🌐 Base URL:")
        volc_base_url_label.setStyleSheet("QLabel { color: #2d3748; background-color: transparent; }")
        self.volc_base_url_input = QLineEdit()
        self.volc_base_url_input.setPlaceholderText("例如: https://ark.cn-beijing.volces.com/api/v3")
        self.volc_base_url_input.setText("https://ark.cn-beijing.volces.com/api/v3")
        self.volc_base_url_input.setMinimumWidth(350)
        volcengine_layout.addRow(volc_base_url_label, self.volc_base_url_input)

        # Collection Name
        volc_collection_label = QLabel("📚 Collection名称:")
        volc_collection_label.setStyleSheet("QLabel { color: #2d3748; background-color: transparent; }")
        self.volc_collection_input = QLineEdit()
        self.volc_collection_input.setPlaceholderText("默认: video_summaries")
        self.volc_collection_input.setText("video_summaries")
        self.volc_collection_input.setMinimumWidth(350)
        volcengine_layout.addRow(volc_collection_label, self.volc_collection_input)

        # Embedding Model
        volc_model_label = QLabel("🤖 Embedding模型:")
        volc_model_label.setStyleSheet("QLabel { color: #2d3748; background-color: transparent; }")
        self.volc_model_input = QLineEdit()
        self.volc_model_input.setPlaceholderText("输入endpoint ID，例如: ep-20241217191853-w54rf")
        self.volc_model_input.setMinimumWidth(350)
        volcengine_layout.addRow(volc_model_label, self.volc_model_input)

        self.volcengine_widget.setLayout(volcengine_layout)
        self.volcengine_widget.setStyleSheet("""
            QGroupBox {
                border: 1px solid #d0dae6;
                border-radius: 8px;
                margin-top: 8px;
                padding: 12px;
                background: white;
            }
        """)
        vector_layout.addRow(self.volcengine_widget)

        vector_group.setLayout(vector_layout)
        layout.addWidget(vector_group)

        # 说明文字
        note_label = QLabel(
            "💡 <b>配置提示</b><br><br>"
            "• 支持所有 OpenAI 兼容的 API（ChatGPT、DeepSeek、Gemini、Claude 等）<br>"
            "• <b>API Key</b> 和 <b>Base URL</b> 为必填项<br>"
            "• <b>Temperature</b> 控制生成的随机性（0.0-2.0，推荐 0.3）<br>"
            "• 段落合并参数影响段落划分效果，可根据视频内容调整"
        )
        note_label.setWordWrap(True)
        note_label.setStyleSheet("""
            QLabel {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #fffbf0, stop:1 #fff8e6);
                border: 2px solid #ffd966;
                border-left: 6px solid #ffb833;
                border-radius: 10px;
                padding: 18px 20px;
                color: #744210;
                font-size: 13px;
                line-height: 1.8;
            }
        """)
        layout.addWidget(note_label)

        # 按钮区域（固定在底部，不滚动）
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        button_layout.setContentsMargins(30, 15, 30, 20)

        self.test_btn = QPushButton("[测试] 测试连接")
        self.test_btn.clicked.connect(self.test_connection)
        self.test_btn.setMinimumHeight(44)
        self.test_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #667eea, stop:1 #5a67d8);
                color: white;
                border: none;
                padding: 12px 28px;
                border-radius: 10px;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #7c8ef5, stop:1 #6b78e3);
                box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
                transform: translateY(-1px);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #5a67d8, stop:1 #4c5ac7);
                transform: translateY(0);
            }
            QPushButton:disabled {
                background: #cbd5e0;
                color: #a0aec0;
            }
        """)

        self.save_btn = QPushButton("💾 保存配置")
        self.save_btn.clicked.connect(self.save_config)
        self.save_btn.setMinimumHeight(44)
        self.save_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #48bb78, stop:1 #38a169);
                color: white;
                border: none;
                padding: 12px 32px;
                border-radius: 10px;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #5ac98a, stop:1 #48bb78);
                box-shadow: 0 4px 12px rgba(72, 187, 120, 0.4);
                transform: translateY(-1px);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #38a169, stop:1 #2f855a);
                transform: translateY(0);
            }
        """)

        self.cancel_btn = QPushButton("[取消] 取消")
        self.cancel_btn.clicked.connect(self.reject)
        self.cancel_btn.setMinimumHeight(44)
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #fc8181, stop:1 #f56565);
                color: white;
                border: none;
                padding: 12px 32px;
                border-radius: 10px;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #feb2b2, stop:1 #fc8181);
                box-shadow: 0 4px 12px rgba(245, 101, 101, 0.4);
                transform: translateY(-1px);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f56565, stop:1 #e53e3e);
                transform: translateY(0);
            }
        """)

        button_layout.addWidget(self.test_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.cancel_btn)

        # 按钮添加到主布局（在滚动区域外，固定在底部）
        main_layout.addLayout(button_layout)

        # 初始化时隐藏火山引擎配置
        self._on_vector_type_changed(0)

    def _on_vector_type_changed(self, index):
        """向量存储类型改变时的处理"""
        # index 0: ChromaDB, 1: 火山引擎
        self.volcengine_widget.setVisible(index == 1)

    def load_config(self):
        """加载配置"""
        try:
            # 从config中读取HearSight配置
            hearsight_cfg = getattr(config, 'hearsight_config', {})

            if not hearsight_cfg:
                return

            # LLM配置
            llm_cfg = hearsight_cfg.get('llm', {})
            if llm_cfg:
                self.api_key_input.setText(llm_cfg.get('api_key', ''))
                self.base_url_input.setText(llm_cfg.get('base_url', 'https://api.openai.com/v1'))
                self.model_combo.setCurrentText(llm_cfg.get('model', 'gpt-3.5-turbo'))
                self.temperature_spin.setValue(llm_cfg.get('temperature', 0.3))
                self.timeout_spin.setValue(llm_cfg.get('timeout', 120))

            # 合并配置
            merge_cfg = hearsight_cfg.get('merge', {})
            if merge_cfg:
                self.max_gap_spin.setValue(merge_cfg.get('max_gap', 2.0))
                self.max_duration_spin.setValue(merge_cfg.get('max_duration', 30.0))
                self.max_chars_spin.setValue(merge_cfg.get('max_chars', 200))

            # 提示词配置（仅当有自定义值时才覆盖默认值）
            prompt_cfg = hearsight_cfg.get('prompts', {})
            if prompt_cfg:
                para_prompt = prompt_cfg.get('paragraph', '').strip()
                if para_prompt:
                    self.para_prompt_input.setPlainText(para_prompt)

                overall_prompt = prompt_cfg.get('overall', '').strip()
                if overall_prompt:
                    self.overall_prompt_input.setPlainText(overall_prompt)

            # 向量化配置
            vector_cfg = hearsight_cfg.get('vector', {})
            if vector_cfg:
                vector_type = vector_cfg.get('type', 'chromadb')
                if vector_type == 'volcengine':
                    self.vector_type_combo.setCurrentIndex(1)
                else:
                    self.vector_type_combo.setCurrentIndex(0)

                # 火山引擎配置
                volc_cfg = vector_cfg.get('volcengine', {})
                if volc_cfg:
                    self.volc_api_key_input.setText(volc_cfg.get('api_key', ''))
                    self.volc_base_url_input.setText(volc_cfg.get('base_url', 'https://ark.cn-beijing.volces.com/api/v3'))
                    self.volc_collection_input.setText(volc_cfg.get('collection_name', 'video_summaries'))
                    self.volc_model_input.setText(volc_cfg.get('embedding_model', ''))

        except Exception as e:
            print(f"加载HearSight配置失败: {e}")

    def save_config(self):
        """保存配置"""
        # 验证必填项
        api_key = self.api_key_input.text().strip()
        base_url = self.base_url_input.text().strip()
        model = self.model_combo.currentText().strip()

        if not api_key:
            QMessageBox.warning(self, "警告", "请输入API Key")
            return

        if not base_url:
            QMessageBox.warning(self, "警告", "请输入Base URL")
            return

        if not model:
            QMessageBox.warning(self, "警告", "请输入Model")
            return

        # 向量化服务验证
        vector_type_index = self.vector_type_combo.currentIndex()
        if vector_type_index == 1:  # 火山引擎
            volc_api_key = self.volc_api_key_input.text().strip()
            if not volc_api_key:
                QMessageBox.warning(self, "警告", "请输入火山引擎API Key")
                return

        # 构建配置
        hearsight_cfg = {
            'llm': {
                'api_key': api_key,
                'base_url': base_url,
                'model': model,
                'temperature': self.temperature_spin.value(),
                'timeout': self.timeout_spin.value()
            },
            'merge': {
                'max_gap': self.max_gap_spin.value(),
                'max_duration': self.max_duration_spin.value(),
                'max_chars': self.max_chars_spin.value()
            },
            'prompts': {
                'paragraph': self.para_prompt_input.toPlainText().strip(),
                'overall': self.overall_prompt_input.toPlainText().strip()
            },
            'vector': {
                'type': 'volcengine' if vector_type_index == 1 else 'chromadb',
                'volcengine': {
                    'api_key': self.volc_api_key_input.text().strip(),
                    'base_url': self.volc_base_url_input.text().strip(),
                    'collection_name': self.volc_collection_input.text().strip(),
                    'embedding_model': self.volc_model_input.text().strip()
                }
            }
        }

        try:
            # 保存到config
            config.hearsight_config = hearsight_cfg

            # 持久化到文件（如果有配置文件路径）
            if hasattr(config, 'ROOT_DIR'):
                import os
                config_path = os.path.join(config.ROOT_DIR, 'hearsight_config.json')
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(hearsight_cfg, f, ensure_ascii=False, indent=2)

            QMessageBox.information(self, "成功", "配置已保存")
            self.config_saved.emit()
            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存配置失败：\n{str(e)}")

    def test_connection(self):
        """测试API连接（使用后台线程，避免UI卡死）"""
        api_key = self.api_key_input.text().strip()
        base_url = self.base_url_input.text().strip()
        model = self.model_combo.currentText().strip()

        if not api_key or not base_url or not model:
            QMessageBox.warning(self, "警告", "请先填写完整的API配置")
            return

        # 检查是否有正在运行的测试
        if self.test_thread and self.test_thread.isRunning():
            QMessageBox.warning(self, "提示", "已有测试正在运行中，请稍候...")
            return

        # 检查是否也要测试向量化服务
        vector_type_index = self.vector_type_combo.currentIndex()
        test_vector = (vector_type_index == 1)  # 火山引擎

        volc_api_key = None
        volc_base_url = None
        volc_model = None

        if test_vector:
            volc_api_key = self.volc_api_key_input.text().strip()
            volc_base_url = self.volc_base_url_input.text().strip()
            volc_model = self.volc_model_input.text().strip()

            if not volc_api_key or not volc_base_url or not volc_model:
                QMessageBox.warning(self, "警告", "请先填写完整的火山引擎向量化配置")
                return

        # 禁用测试按钮，显示进度
        self.test_btn.setEnabled(False)
        self.test_btn.setText("测试中...")

        # 创建测试线程
        self.test_thread = ConnectionTestThread(
            api_key=api_key,
            base_url=base_url,
            model=model,
            test_vector=test_vector,
            volc_api_key=volc_api_key,
            volc_base_url=volc_base_url,
            volc_model=volc_model
        )

        # 连接信号
        self.test_thread.finished.connect(self.on_test_finished)

        # 启动线程
        self.test_thread.start()

    def on_test_finished(self, success: bool, message: str):
        """测试完成的回调"""
        # 恢复测试按钮
        self.test_btn.setEnabled(True)
        self.test_btn.setText("[测试] 测试连接")

        # 显示结果
        if success:
            QMessageBox.information(self, "测试完成", message)
        else:
            QMessageBox.critical(self, "测试失败", message)

    def get_config(self) -> dict:
        """获取当前配置"""
        return {
            'llm': {
                'api_key': self.api_key_input.text().strip(),
                'base_url': self.base_url_input.text().strip(),
                'model': self.model_combo.currentText().strip(),
                'temperature': self.temperature_spin.value(),
                'timeout': self.timeout_spin.value()
            },
            'merge': {
                'max_gap': self.max_gap_spin.value(),
                'max_duration': self.max_duration_spin.value(),
                'max_chars': self.max_chars_spin.value()
            }
        }
