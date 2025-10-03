"""
HearSight配置对话框

配置LLM API参数
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QComboBox, QPushButton, QLabel,
    QGroupBox, QSpinBox, QDoubleSpinBox, QMessageBox
)
from PySide6.QtCore import Qt, Signal
from videotrans.configure import config
import json


class HearSightConfigDialog(QDialog):
    """HearSight配置对话框"""

    config_saved = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("HearSight配置")
        self.resize(700, 600)
        self.setStyleSheet("""
            QDialog {
                background-color: #f8f9fa;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 20px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 8px;
                color: #2c3e50;
                font-size: 14px;
            }
            QLabel {
                color: #495057;
                font-size: 13px;
            }
            QLineEdit {
                border: 2px solid #e0e0e0;
                border-radius: 6px;
                padding: 10px;
                background-color: white;
                font-size: 13px;
                color: #2c3e50;
            }
            QLineEdit:focus {
                border-color: #4a9eff;
            }
            QComboBox {
                border: 2px solid #e0e0e0;
                border-radius: 6px;
                padding: 8px;
                background-color: white;
                font-size: 13px;
            }
            QComboBox:focus {
                border-color: #4a9eff;
            }
            QDoubleSpinBox, QSpinBox {
                border: 2px solid #e0e0e0;
                border-radius: 6px;
                padding: 8px;
                background-color: white;
                font-size: 13px;
            }
            QDoubleSpinBox:focus, QSpinBox:focus {
                border-color: #4a9eff;
            }
        """)

        self.init_ui()
        self.load_config()

    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(25, 25, 25, 25)

        # LLM API配置组
        llm_group = QGroupBox("  🤖  LLM API 配置")
        llm_layout = QFormLayout()

        # API Key
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.Password)
        self.api_key_input.setPlaceholderText("输入你的API密钥")
        llm_layout.addRow("API Key *:", self.api_key_input)

        # Base URL
        self.base_url_input = QLineEdit()
        self.base_url_input.setPlaceholderText("例如: https://api.openai.com/v1")
        self.base_url_input.setText("https://api.openai.com/v1")
        llm_layout.addRow("Base URL *:", self.base_url_input)

        # Model
        self.model_combo = QComboBox()
        self.model_combo.setEditable(True)
        self.model_combo.addItems([
            "gpt-3.5-turbo",
            "gpt-4",
            "gpt-4-turbo",
            "deepseek-chat",
            "gemini-pro",
            "claude-3-sonnet",
        ])
        llm_layout.addRow("Model *:", self.model_combo)

        # Temperature
        self.temperature_spin = QDoubleSpinBox()
        self.temperature_spin.setRange(0.0, 2.0)
        self.temperature_spin.setSingleStep(0.1)
        self.temperature_spin.setValue(0.3)
        self.temperature_spin.setDecimals(1)
        llm_layout.addRow("Temperature:", self.temperature_spin)

        # Timeout
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(10, 300)
        self.timeout_spin.setSingleStep(10)
        self.timeout_spin.setValue(120)
        self.timeout_spin.setSuffix(" 秒")
        llm_layout.addRow("超时时间:", self.timeout_spin)

        llm_group.setLayout(llm_layout)
        layout.addWidget(llm_group)

        # 段落合并配置组
        merge_group = QGroupBox("  📐  段落合并参数")
        merge_layout = QFormLayout()

        # 最大时间间隔
        self.max_gap_spin = QDoubleSpinBox()
        self.max_gap_spin.setRange(0.5, 10.0)
        self.max_gap_spin.setSingleStep(0.5)
        self.max_gap_spin.setValue(2.0)
        self.max_gap_spin.setDecimals(1)
        self.max_gap_spin.setSuffix(" 秒")
        merge_layout.addRow("最大时间间隔:", self.max_gap_spin)

        # 最大段落时长
        self.max_duration_spin = QDoubleSpinBox()
        self.max_duration_spin.setRange(10.0, 120.0)
        self.max_duration_spin.setSingleStep(5.0)
        self.max_duration_spin.setValue(30.0)
        self.max_duration_spin.setDecimals(0)
        self.max_duration_spin.setSuffix(" 秒")
        merge_layout.addRow("最大段落时长:", self.max_duration_spin)

        # 最大字符数
        self.max_chars_spin = QSpinBox()
        self.max_chars_spin.setRange(50, 1000)
        self.max_chars_spin.setSingleStep(50)
        self.max_chars_spin.setValue(200)
        merge_layout.addRow("最大字符数:", self.max_chars_spin)

        merge_group.setLayout(merge_layout)
        layout.addWidget(merge_group)

        # 说明文字
        note_label = QLabel(
            "💡 提示：\n"
            "• 支持所有OpenAI兼容的API（ChatGPT、DeepSeek、Gemini等）\n"
            "• API Key 为必填项\n"
            "• 段落合并参数影响段落划分效果，可根据需要调整"
        )
        note_label.setStyleSheet("""
            QLabel {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #fff9e6, stop:1 #fff3d9);
                border: 2px solid #ffd966;
                border-left: 5px solid #ffb833;
                border-radius: 8px;
                padding: 15px;
                color: #856404;
                font-size: 13px;
                line-height: 1.6;
            }
        """)
        layout.addWidget(note_label)

        # 按钮区域
        button_layout = QHBoxLayout()

        self.test_btn = QPushButton("测试连接")
        self.test_btn.clicked.connect(self.test_connection)
        self.test_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #7c8a99, stop:1 #6c757d);
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 8px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #8a98a7, stop:1 #7a8290);
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #5a6268, stop:1 #4a5258);
            }
            QPushButton:disabled {
                background: #cccccc;
                color: #666666;
            }
        """)

        self.save_btn = QPushButton("保存")
        self.save_btn.clicked.connect(self.save_config)
        self.save_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #34ce57, stop:1 #28a745);
                color: white;
                border: none;
                padding: 12px 28px;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #40d967, stop:1 #2dbd4e);
                box-shadow: 0 4px 12px rgba(40, 167, 69, 0.4);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #218838, stop:1 #1e7e34);
            }
        """)

        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.clicked.connect(self.reject)
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #e54858, stop:1 #dc3545);
                color: white;
                border: none;
                padding: 12px 28px;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ed5a68, stop:1 #e04555);
                box-shadow: 0 4px 12px rgba(220, 53, 69, 0.4);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #c82333, stop:1 #b21f2d);
            }
        """)

        button_layout.addWidget(self.test_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.cancel_btn)

        layout.addLayout(button_layout)

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
        """测试API连接"""
        api_key = self.api_key_input.text().strip()
        base_url = self.base_url_input.text().strip()
        model = self.model_combo.currentText().strip()

        if not api_key or not base_url or not model:
            QMessageBox.warning(self, "警告", "请先填写完整的API配置")
            return

        try:
            # 测试调用
            from videotrans.hearsight.chat_client import chat_simple

            self.test_btn.setEnabled(False)
            self.test_btn.setText("测试中...")

            response = chat_simple(
                prompt="请用一句话回复：你好",
                api_key=api_key,
                base_url=base_url,
                model=model,
                timeout=30
            )

            QMessageBox.information(
                self,
                "测试成功",
                f"API连接正常！\n\n模型响应：{response[:100]}"
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                "测试失败",
                f"API连接失败：\n{str(e)}"
            )

        finally:
            self.test_btn.setEnabled(True)
            self.test_btn.setText("测试连接")

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
