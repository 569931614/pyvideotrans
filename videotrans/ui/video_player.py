"""
内嵌视频播放器
使用Qt Multimedia实现视频播放和时间跳转
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
    QSlider, QLabel, QStyle, QSizePolicy
)
from PySide6.QtCore import Qt, QUrl, Signal
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget


class VideoPlayerDialog(QDialog):
    """视频播放器对话框"""
    
    # 信号：播放位置改变
    position_changed = Signal(int)  # 毫秒
    
    def __init__(self, video_path: str, start_time: float = 0, parent=None):
        """
        初始化视频播放器

        Args:
            video_path: 视频文件路径
            start_time: 开始播放时间（秒）
            parent: 父窗口
        """
        super().__init__(parent)
        self.video_path = video_path
        self.start_time = start_time
        self.has_seeked = False  # 标记是否已经跳转过

        print(f"\n🎬 初始化视频播放器...")
        print(f"   视频路径: {video_path}")
        print(f"   开始时间: {start_time}秒")

        self.setWindowTitle("视频播放器")
        self.resize(960, 600)

        # 创建媒体播放器
        self.player = QMediaPlayer(self)
        self.audio_output = QAudioOutput(self)
        self.player.setAudioOutput(self.audio_output)

        # 创建视频显示控件
        self.video_widget = QVideoWidget(self)
        self.player.setVideoOutput(self.video_widget)

        # 初始化UI
        self.init_ui()

        # 连接信号
        self.player.positionChanged.connect(self.on_position_changed)
        self.player.durationChanged.connect(self.on_duration_changed)
        self.player.playbackStateChanged.connect(self.on_state_changed)
        self.player.mediaStatusChanged.connect(self.on_media_status_changed)

        # 加载视频
        self.load_video()
    
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 视频显示区域
        self.video_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.video_widget)
        
        # 控制栏
        control_layout = QHBoxLayout()
        control_layout.setContentsMargins(10, 5, 10, 5)
        
        # 播放/暂停按钮
        self.play_btn = QPushButton()
        self.play_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.play_btn.clicked.connect(self.toggle_play)
        self.play_btn.setFixedSize(40, 40)
        control_layout.addWidget(self.play_btn)
        
        # 停止按钮
        self.stop_btn = QPushButton()
        self.stop_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaStop))
        self.stop_btn.clicked.connect(self.stop)
        self.stop_btn.setFixedSize(40, 40)
        control_layout.addWidget(self.stop_btn)
        
        # 时间标签
        self.time_label = QLabel("00:00 / 00:00")
        self.time_label.setMinimumWidth(120)
        control_layout.addWidget(self.time_label)
        
        # 进度条
        self.position_slider = QSlider(Qt.Horizontal)
        self.position_slider.setRange(0, 0)
        self.position_slider.sliderMoved.connect(self.set_position)
        control_layout.addWidget(self.position_slider)
        
        # 音量控制
        volume_label = QLabel("🔊")
        control_layout.addWidget(volume_label)
        
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(70)
        self.volume_slider.setMaximumWidth(100)
        self.volume_slider.valueChanged.connect(self.set_volume)
        control_layout.addWidget(self.volume_slider)
        
        # 全屏按钮
        self.fullscreen_btn = QPushButton()
        self.fullscreen_btn.setIcon(self.style().standardIcon(QStyle.SP_TitleBarMaxButton))
        self.fullscreen_btn.clicked.connect(self.toggle_fullscreen)
        self.fullscreen_btn.setFixedSize(40, 40)
        control_layout.addWidget(self.fullscreen_btn)
        
        layout.addLayout(control_layout)
        
        # 设置样式
        self.setStyleSheet("""
            QDialog {
                background-color: #1a1a1a;
            }
            QPushButton {
                background-color: #2a2a2a;
                border: none;
                border-radius: 5px;
                color: white;
            }
            QPushButton:hover {
                background-color: #3a3a3a;
            }
            QPushButton:pressed {
                background-color: #4a4a4a;
            }
            QSlider::groove:horizontal {
                border: 1px solid #999999;
                height: 8px;
                background: #2a2a2a;
                margin: 2px 0;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #4a9eff;
                border: 1px solid #5c5c5c;
                width: 18px;
                margin: -5px 0;
                border-radius: 9px;
            }
            QSlider::handle:horizontal:hover {
                background: #5aa9ff;
            }
            QLabel {
                color: white;
                padding: 0 5px;
            }
        """)
    
    def load_video(self):
        """加载视频（支持本地文件和URL）"""
        print(f"📂 加载视频: {self.video_path}")

        # 检查是否是URL（http/https）
        if self.video_path.startswith(('http://', 'https://')):
            # URL格式：直接使用QUrl
            print(f"   类型: 在线视频 (URL)")
            video_url = QUrl(self.video_path)
        else:
            # 本地文件：使用fromLocalFile
            print(f"   类型: 本地文件")
            video_url = QUrl.fromLocalFile(self.video_path)

        print(f"   QUrl: {video_url.toString()}")
        self.player.setSource(video_url)

        # 设置初始音量
        self.set_volume(70)
        print(f"✅ 视频加载命令已发送")
    
    def toggle_play(self):
        """切换播放/暂停"""
        if self.player.playbackState() == QMediaPlayer.PlayingState:
            self.player.pause()
        else:
            self.player.play()
    
    def stop(self):
        """停止播放"""
        self.player.stop()
    
    def set_position(self, position):
        """设置播放位置"""
        self.player.setPosition(position)
    
    def set_volume(self, volume):
        """设置音量"""
        self.audio_output.setVolume(volume / 100.0)
    
    def toggle_fullscreen(self):
        """切换全屏"""
        if self.isFullScreen():
            self.showNormal()
            self.fullscreen_btn.setIcon(self.style().standardIcon(QStyle.SP_TitleBarMaxButton))
        else:
            self.showFullScreen()
            self.fullscreen_btn.setIcon(self.style().standardIcon(QStyle.SP_TitleBarNormalButton))
    
    def on_position_changed(self, position):
        """播放位置改变"""
        self.position_slider.setValue(position)
        self.update_time_label()
        self.position_changed.emit(position)
    
    def on_duration_changed(self, duration):
        """视频时长改变"""
        print(f"⏱️ 视频时长: {duration}ms ({duration/1000:.2f}秒)")
        self.position_slider.setRange(0, duration)
        self.update_time_label()

        # 如果设置了开始时间且还没跳转过，跳转到该位置
        if self.start_time > 0 and not self.has_seeked:
            seek_position = int(self.start_time * 1000)
            print(f"⏩ 跳转到: {seek_position}ms ({self.start_time}秒)")
            self.player.setPosition(seek_position)
            self.has_seeked = True
            # 自动开始播放
            print(f"▶️ 开始播放...")
            self.player.play()
    
    def on_state_changed(self, state):
        """播放状态改变"""
        state_names = {
            QMediaPlayer.StoppedState: "停止",
            QMediaPlayer.PlayingState: "播放中",
            QMediaPlayer.PausedState: "暂停"
        }
        print(f"🎵 播放状态: {state_names.get(state, '未知')}")

        if state == QMediaPlayer.PlayingState:
            self.play_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))
        else:
            self.play_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))

    def on_media_status_changed(self, status):
        """媒体状态改变"""
        status_names = {
            QMediaPlayer.NoMedia: "无媒体",
            QMediaPlayer.LoadingMedia: "加载中",
            QMediaPlayer.LoadedMedia: "已加载",
            QMediaPlayer.StalledMedia: "停滞",
            QMediaPlayer.BufferingMedia: "缓冲中",
            QMediaPlayer.BufferedMedia: "已缓冲",
            QMediaPlayer.EndOfMedia: "播放结束",
            QMediaPlayer.InvalidMedia: "无效媒体"
        }
        print(f"📡 媒体状态: {status_names.get(status, '未知')}")

        # 当媒体加载完成且还没跳转时，执行跳转
        if status == QMediaPlayer.LoadedMedia and self.start_time > 0 and not self.has_seeked:
            seek_position = int(self.start_time * 1000)
            print(f"⏩ [LoadedMedia] 跳转到: {seek_position}ms ({self.start_time}秒)")
            self.player.setPosition(seek_position)
            self.has_seeked = True
            print(f"▶️ [LoadedMedia] 开始播放...")
            self.player.play()
    
    def update_time_label(self):
        """更新时间标签"""
        position = self.player.position() // 1000  # 转换为秒
        duration = self.player.duration() // 1000
        
        position_str = f"{position // 60:02d}:{position % 60:02d}"
        duration_str = f"{duration // 60:02d}:{duration % 60:02d}"
        
        self.time_label.setText(f"{position_str} / {duration_str}")
    
    def seek_to(self, time_seconds: float):
        """
        跳转到指定时间
        
        Args:
            time_seconds: 时间（秒）
        """
        self.player.setPosition(int(time_seconds * 1000))
        if self.player.playbackState() != QMediaPlayer.PlayingState:
            self.player.play()
    
    def keyPressEvent(self, event):
        """键盘事件"""
        if event.key() == Qt.Key_Space:
            self.toggle_play()
        elif event.key() == Qt.Key_Escape and self.isFullScreen():
            self.showNormal()
            self.fullscreen_btn.setIcon(self.style().standardIcon(QStyle.SP_TitleBarMaxButton))
        elif event.key() == Qt.Key_F:
            self.toggle_fullscreen()
        elif event.key() == Qt.Key_Left:
            # 后退5秒
            self.player.setPosition(max(0, self.player.position() - 5000))
        elif event.key() == Qt.Key_Right:
            # 前进5秒
            self.player.setPosition(min(self.player.duration(), self.player.position() + 5000))
        elif event.key() == Qt.Key_Up:
            # 增加音量
            self.volume_slider.setValue(min(100, self.volume_slider.value() + 10))
        elif event.key() == Qt.Key_Down:
            # 减少音量
            self.volume_slider.setValue(max(0, self.volume_slider.value() - 10))
        else:
            super().keyPressEvent(event)
    
    def closeEvent(self, event):
        """关闭事件"""
        self.player.stop()
        super().closeEvent(event)

