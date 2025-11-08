# -*- coding: utf-8 -*-
"""
OSS 配置对话框

配置阿里云 OSS 上传参数
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QComboBox, QPushButton, QLabel,
    QGroupBox, QCheckBox, QMessageBox, QSpinBox, QFileDialog
)
from PySide6.QtCore import Qt, Signal, QThread
from videotrans.configure import config
from videotrans.configure.oss_config import get_oss_config_manager
import json


class OSSConnectionTestThread(QThread):
    """后台测试 OSS 连接线程"""
    finished = Signal(bool, str)  # success, message

    def __init__(self, oss_config):
        super().__init__()
        self.oss_config = oss_config

    def run(self):
        try:
            manager = get_oss_config_manager()
            success, message = manager.test_connection(self.oss_config)
            self.finished.emit(success, message)
        except Exception as e:
            self.finished.emit(False, f"测试失败: {str(e)}")


class OSSConfigDialog(QDialog):
    """OSS 配置对话框"""

    config_saved = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        # 保存测试线程引用
        self.test_thread = None

        self.setWindowTitle("OSS 对象存储配置")
        self.resize(700, 600)
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
                subcontrol-position: top left;
                padding: 8px 16px;
                color: #2c5282;
                font-size: 14px;
            }
            QLabel {
                color: #2d3748;
                font-size: 13px;
            }
            QLineEdit {
                padding: 8px 12px;
                border: 2px solid #cbd5e0;
                border-radius: 6px;
                background: white;
                font-size: 13px;
            }
            QLineEdit:focus {
                border-color: #4299e1;
            }
            QCheckBox {
                spacing: 8px;
                color: #2d3748;
                font-size: 13px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 4px;
            }
            QPushButton {
                padding: 10px 20px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 13px;
                min-width: 100px;
            }
            QPushButton#primaryBtn {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #4299e1, stop:1 #3182ce);
                color: white;
                border: none;
            }
            QPushButton#primaryBtn:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3182ce, stop:1 #2c5282);
            }
            QPushButton#secondaryBtn {
                background: white;
                color: #2d3748;
                border: 2px solid #cbd5e0;
            }
            QPushButton#secondaryBtn:hover {
                background: #f7fafc;
                border-color: #a0aec0;
            }
        """)

        self.init_ui()
        self.load_config()

    def init_ui(self):
        """初始化 UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)

        # 启用开关
        enable_group = QGroupBox("功能开关")
        enable_layout = QVBoxLayout()
        self.enable_checkbox = QCheckBox("启用 OSS 上传功能")
        self.enable_checkbox.stateChanged.connect(self._on_enable_changed)
        enable_layout.addWidget(self.enable_checkbox)

        self.auto_upload_checkbox = QCheckBox("视频处理完成后自动上传")
        enable_layout.addWidget(self.auto_upload_checkbox)

        enable_group.setLayout(enable_layout)
        layout.addWidget(enable_group)

        # OSS 连接配置
        oss_group = QGroupBox("对象存储配置")
        oss_form = QFormLayout()
        oss_form.setSpacing(12)
        oss_form.setContentsMargins(20, 20, 20, 20)

        # 提供商选择
        self.provider_combo = QComboBox()
        self.provider_combo.addItem("阿里云 OSS", "aliyun")
        self.provider_combo.addItem("AWS S3", "aws")
        self.provider_combo.addItem("MinIO / 自定义 S3", "minio")
        self.provider_combo.currentIndexChanged.connect(self._on_provider_changed)
        oss_form.addRow("提供商:", self.provider_combo)

        # Endpoint
        self.endpoint_edit = QLineEdit()
        self.endpoint_edit.setPlaceholderText("例如: oss-cn-beijing.aliyuncs.com")
        oss_form.addRow("Endpoint:", self.endpoint_edit)

        # Bucket 名称
        self.bucket_edit = QLineEdit()
        self.bucket_edit.setPlaceholderText("例如: my-video-bucket")
        oss_form.addRow("Bucket 名称:", self.bucket_edit)

        # Access Key ID
        self.access_key_id_edit = QLineEdit()
        self.access_key_id_edit.setPlaceholderText("输入 Access Key ID")
        oss_form.addRow("Access Key ID:", self.access_key_id_edit)

        # Access Key Secret
        self.access_key_secret_edit = QLineEdit()
        self.access_key_secret_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.access_key_secret_edit.setPlaceholderText("输入 Access Key Secret")
        oss_form.addRow("Access Key Secret:", self.access_key_secret_edit)

        # Region (可选)
        self.region_edit = QLineEdit()
        self.region_edit.setPlaceholderText("例如: cn-beijing (可选)")
        oss_form.addRow("Region:", self.region_edit)

        # 使用 HTTP (仅 MinIO)
        self.use_http_checkbox = QCheckBox("使用 HTTP (不使用 HTTPS)")
        oss_form.addRow("协议:", self.use_http_checkbox)

        # 自定义域名 (可选)
        self.custom_domain_edit = QLineEdit()
        self.custom_domain_edit.setPlaceholderText("例如: https://cdn.example.com (可选)")
        oss_form.addRow("自定义域名:", self.custom_domain_edit)

        # 路径前缀
        self.path_prefix_edit = QLineEdit()
        self.path_prefix_edit.setText("videos/")
        self.path_prefix_edit.setPlaceholderText("例如: videos/")
        oss_form.addRow("上传路径前缀:", self.path_prefix_edit)

        oss_group.setLayout(oss_form)
        layout.addWidget(oss_group)

        # 高级选项
        advanced_group = QGroupBox("高级选项")
        advanced_form = QFormLayout()
        advanced_form.setSpacing(12)
        advanced_form.setContentsMargins(20, 20, 20, 20)

        self.public_access_checkbox = QCheckBox("公网可访问")
        self.public_access_checkbox.setChecked(True)
        advanced_form.addRow("访问权限:", self.public_access_checkbox)

        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(60, 3600)
        self.timeout_spin.setValue(300)
        self.timeout_spin.setSuffix(" 秒")
        advanced_form.addRow("上传超时:", self.timeout_spin)

        self.retry_spin = QSpinBox()
        self.retry_spin.setRange(0, 10)
        self.retry_spin.setValue(3)
        self.retry_spin.setSuffix(" 次")
        advanced_form.addRow("失败重试:", self.retry_spin)

        advanced_group.setLayout(advanced_form)
        layout.addWidget(advanced_group)

        # 按钮区域
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.test_btn = QPushButton("测试连接")
        self.test_btn.setObjectName("secondaryBtn")
        self.test_btn.clicked.connect(self._test_connection)
        btn_layout.addWidget(self.test_btn)

        self.save_btn = QPushButton("保存配置")
        self.save_btn.setObjectName("primaryBtn")
        self.save_btn.clicked.connect(self._save_config)
        btn_layout.addWidget(self.save_btn)

        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.setObjectName("secondaryBtn")
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)

        layout.addLayout(btn_layout)

        # 提示信息
        tip_label = QLabel(
            "💡 提示：Access Key Secret 将被加密存储。"
            "建议使用 RAM 子账号并限制最小权限。"
        )
        tip_label.setWordWrap(True)
        tip_label.setStyleSheet("color: #718096; font-size: 12px; padding: 10px;")
        layout.addWidget(tip_label)

    def _on_enable_changed(self, state):
        """启用状态改变"""
        enabled = state == Qt.CheckState.Checked.value
        # 启用/禁用所有输入控件
        for widget in [
            self.provider_combo, self.endpoint_edit, self.bucket_edit,
            self.access_key_id_edit, self.access_key_secret_edit,
            self.region_edit, self.use_http_checkbox, self.custom_domain_edit,
            self.path_prefix_edit, self.auto_upload_checkbox,
            self.public_access_checkbox, self.timeout_spin,
            self.retry_spin, self.test_btn
        ]:
            widget.setEnabled(enabled)

    def _on_provider_changed(self, index):
        """提供商改变时更新 UI"""
        provider = self.provider_combo.currentData()

        if provider == "aliyun":
            self.endpoint_edit.setPlaceholderText("例如: oss-cn-beijing.aliyuncs.com")
            self.region_edit.setPlaceholderText("例如: cn-beijing (可选)")
            self.use_http_checkbox.setVisible(False)
            self.region_edit.setVisible(True)
        elif provider == "aws":
            self.endpoint_edit.setPlaceholderText("留空使用默认 S3 endpoint")
            self.region_edit.setPlaceholderText("例如: us-east-1 (必填)")
            self.use_http_checkbox.setVisible(False)
            self.region_edit.setVisible(True)
        elif provider == "minio":
            self.endpoint_edit.setPlaceholderText("例如: minio.example.com:9000")
            self.region_edit.setVisible(False)
            self.use_http_checkbox.setVisible(True)

    def load_config(self):
        """加载现有配置"""
        try:
            manager = get_oss_config_manager()
            config_data = manager.load_config()

            self.enable_checkbox.setChecked(config_data.get('enabled', False))

            # 设置提供商
            provider = config_data.get('provider', 'aliyun')
            for i in range(self.provider_combo.count()):
                if self.provider_combo.itemData(i) == provider:
                    self.provider_combo.setCurrentIndex(i)
                    break

            self.endpoint_edit.setText(config_data.get('endpoint', ''))
            self.bucket_edit.setText(config_data.get('bucket_name', ''))
            self.access_key_id_edit.setText(config_data.get('access_key_id', ''))
            self.access_key_secret_edit.setText(config_data.get('access_key_secret', ''))
            self.region_edit.setText(config_data.get('region', ''))
            self.use_http_checkbox.setChecked(config_data.get('use_http', False))
            self.custom_domain_edit.setText(config_data.get('custom_domain', ''))
            self.path_prefix_edit.setText(config_data.get('path_prefix', 'videos/'))
            self.auto_upload_checkbox.setChecked(config_data.get('upload_on_complete', True))
            self.public_access_checkbox.setChecked(config_data.get('public_access', True))
            self.timeout_spin.setValue(config_data.get('upload_timeout', 300))
            self.retry_spin.setValue(config_data.get('retry_count', 3))

            # 触发启用状态检查
            self._on_enable_changed(self.enable_checkbox.checkState().value)
            # 触发提供商 UI 更新
            self._on_provider_changed(self.provider_combo.currentIndex())

        except Exception as e:
            config.logger.error(f"加载 OSS 配置失败: {e}")

    def _get_config_data(self) -> dict:
        """获取当前配置数据"""
        return {
            "enabled": self.enable_checkbox.isChecked(),
            "provider": self.provider_combo.currentData(),
            "endpoint": self.endpoint_edit.text().strip(),
            "bucket_name": self.bucket_edit.text().strip(),
            "access_key_id": self.access_key_id_edit.text().strip(),
            "access_key_secret": self.access_key_secret_edit.text().strip(),
            "region": self.region_edit.text().strip(),
            "use_http": self.use_http_checkbox.isChecked(),
            "custom_domain": self.custom_domain_edit.text().strip(),
            "path_prefix": self.path_prefix_edit.text().strip(),
            "public_access": self.public_access_checkbox.isChecked(),
            "upload_on_complete": self.auto_upload_checkbox.isChecked(),
            "upload_timeout": self.timeout_spin.value(),
            "retry_count": self.retry_spin.value(),
            "multipart_threshold": 104857600  # 100MB
        }

    def _test_connection(self):
        """测试 OSS 连接"""
        if not self.enable_checkbox.isChecked():
            QMessageBox.warning(self, "提示", "请先启用 OSS 上传功能")
            return

        config_data = self._get_config_data()

        # 禁用测试按钮
        self.test_btn.setEnabled(False)
        self.test_btn.setText("测试中...")

        # 创建测试线程
        self.test_thread = OSSConnectionTestThread(config_data)
        self.test_thread.finished.connect(self._on_test_finished)
        self.test_thread.start()

    def _on_test_finished(self, success: bool, message: str):
        """测试完成回调"""
        self.test_btn.setEnabled(True)
        self.test_btn.setText("测试连接")

        if success:
            QMessageBox.information(self, "测试成功", message)
        else:
            QMessageBox.warning(self, "测试失败", message)

    def _save_config(self):
        """保存配置"""
        config_data = self._get_config_data()

        # 如果启用了，验证配置
        if config_data['enabled']:
            manager = get_oss_config_manager()
            valid, msg = manager.validate_config(config_data)
            if not valid:
                QMessageBox.warning(self, "配置错误", f"配置验证失败:\n{msg}")
                return

        # 保存配置
        try:
            manager = get_oss_config_manager()
            if manager.save_config(config_data):
                QMessageBox.information(self, "成功", "OSS 配置已保存")
                self.config_saved.emit()
                self.accept()
            else:
                QMessageBox.warning(self, "错误", "保存配置失败")

        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存配置时出错:\n{str(e)}")
