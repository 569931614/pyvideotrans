from __future__ import annotations

import os

from PySide6.QtCore import QUrl
from PySide6.QtWidgets import QWidget, QVBoxLayout, QMessageBox, QPushButton, QHBoxLayout

try:
    from PySide6.QtWebEngineWidgets import QWebEngineView
    from PySide6.QtWebChannel import QWebChannel
    from PySide6.QtWebEngineCore import QWebEngineSettings
except Exception:  # pragma: no cover - optional dependency at runtime
    QWebEngineView = None  # type: ignore
    QWebChannel = None  # type: ignore
    QWebEngineSettings = None  # type: ignore

from videotrans.configure import config
from videotrans.ui.webbridge import WebBridge


class HtmlMainView(QWidget):
    """A container widget hosting QWebEngineView and WebChannel bridge."""

    def __init__(self, main_window):
        super().__init__(parent=main_window)
        self._main_window = main_window
        self.setWindowTitle("HTML UI - 新界面预览")
        self.dev_tools = None

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        if QWebEngineView is None or QWebChannel is None:
            QMessageBox.critical(
                main_window,
                "缺少组件",
                "当前环境未安装 Qt WebEngine 组件，无法加载 HTML UI。\n"
                "请安装 PySide6-WebEngine 或使用 pip 安装包含 WebEngine 的 PySide6 版本。",
            )
            self.setDisabled(True)
            return

        # Add debug toolbar
        toolbar = QHBoxLayout()
        toolbar.setContentsMargins(5, 5, 5, 5)

        reload_btn = QPushButton("🔄 刷新页面")
        reload_btn.clicked.connect(self.reload_page)
        toolbar.addWidget(reload_btn)

        debug_btn = QPushButton("🔍 开发者工具")
        debug_btn.clicked.connect(self.toggle_dev_tools)
        toolbar.addWidget(debug_btn)

        console_btn = QPushButton("📋 查看Console")
        console_btn.clicked.connect(self.open_console_in_terminal)
        toolbar.addWidget(console_btn)

        toolbar.addStretch()

        main_layout.addLayout(toolbar)

        self.web = QWebEngineView(self)
        main_layout.addWidget(self.web)

        # Enable developer tools
        try:
            settings = self.web.settings()
            settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
            settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True)
            settings.setAttribute(QWebEngineSettings.WebAttribute.ErrorPageEnabled, True)
            settings.setAttribute(QWebEngineSettings.WebAttribute.PluginsEnabled, True)
            settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
            settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanOpenWindows, True)
        except Exception as e:
            print(f"Warning: Could not configure WebEngine settings: {e}")

        # Setup channel and bridge
        self.channel = QWebChannel(self.web)
        self.bridge = WebBridge(main_window)
        self.channel.registerObject("bridge", self.bridge)
        self.web.page().setWebChannel(self.channel)

        # Capture console messages
        self.web.page().javaScriptConsoleMessage = self.handle_js_console

        # Load local index.html
        html_path = os.path.join(config.ROOT_DIR, "videotrans", "webui", "index.html")
        print(f"Loading HTML UI from: {html_path}")
        if not os.path.exists(html_path):
            print(f"ERROR: HTML file not found at {html_path}")
        self.web.setUrl(QUrl.fromLocalFile(html_path))

    def handle_js_console(self, level, message, line, source):
        """Capture JavaScript console messages"""
        level_map = {0: "DEBUG", 1: "INFO", 2: "WARNING", 3: "ERROR"}
        level_str = level_map.get(level, "UNKNOWN")
        print(f"[JS {level_str}] {message} (Line {line} in {source})")

    def reload_page(self):
        """Reload the current page"""
        self.web.reload()
        print("Page reloaded")

    def toggle_dev_tools(self):
        """Toggle developer tools window"""
        try:
            from PySide6.QtWebEngineWidgets import QWebEngineView
            if self.dev_tools is None:
                self.dev_tools = QWebEngineView()
                self.dev_tools.setWindowTitle("开发者工具 - HTML UI")
                self.dev_tools.resize(1200, 800)
                self.web.page().setDevToolsPage(self.dev_tools.page())

            if self.dev_tools.isVisible():
                self.dev_tools.hide()
            else:
                self.dev_tools.show()
        except Exception as e:
            QMessageBox.warning(self, "提示", f"无法打开开发者工具：\n{str(e)}")

    def open_console_in_terminal(self):
        """Open a dialog showing console logs"""
        QMessageBox.information(
            self,
            "Console日志",
            "JavaScript Console输出已在终端/控制台中显示。\n\n"
            "请查看运行程序的命令行窗口。\n\n"
            "或点击 '🔍 开发者工具' 按钮打开完整的开发者工具。"
        )


