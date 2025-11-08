import os
import platform
import re
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Dict, List, Any

from PySide6 import QtWidgets
from PySide6.QtCore import QTimer, Qt

from videotrans.configure import config
from videotrans.util import tools
from videotrans.util.ListenVoice import ListenVoice


@dataclass
class WinActionSub:
    main: Optional[Any] = None

    update_btn: Optional[Any] = field(default=None, init=False)
    edit_subtitle_type: str = field(default='edit_subtitle_source', init=False)
    wait_subtitle: str = field(default='', init=False)
    is_render: bool = field(default=False, init=False)
    is_batch: bool = field(default=True, init=False)
    removing_layout: bool = field(default=False, init=False)

    # -- UI 对象实例 --
    scroll_area: Optional[Any] = field(default=None, init=False)
    scroll_area_after: Optional[Any] = field(default=None, init=False)
    scroll_area_search: Optional[Any] = field(default=None, init=False)

    # -- 数据容器 (使用 default_factory 处理可变类型) --
    processbtns: Dict = field(default_factory=dict, init=False)
    obj_list: List[Dict] = field(default_factory=list, init=False)
    cfg: Dict = field(default_factory=dict, init=False)
    queue_mp4: List[str] = field(default_factory=list, init=False)

    def show_model_help(self):

        msg = "从 tiny 到 base -> small -> medium -> large-v3 模型，识别效果越来越好，但模型体积越来越大，识别速度越来越慢，需要更多CPU/内存/GPU资源。\n默认使用tiny模型，如果想要更好的效果，请使用更大模型\n\n .en 后缀模型和 distil 开头的模型只用于识别英文发音视频\n"
        if config.defaulelang != 'zh':
            msg = 'From tiny model to base to small to medium to large-v3 model, the recognition effect is getting better and better, but the model size is getting bigger and bigger, the recognition speed is getting slower and slower, and it needs more CPU/memory/GPU resources. \n default is to use tiny model, if you want better result, please use bigger model \n\n.en suffix model and model starting with distil is only used to recognize English pronunciation video\n'

        # 创建 QMessageBox
        msg_box = QtWidgets.QMessageBox(self.main)
        msg_box.setWindowTitle("Help")
        msg_box.setText(msg)

        # 添加 OK 按钮
        ok_button = msg_box.addButton(QtWidgets.QMessageBox.Ok)
        ok_button.setText("知道了" if config.defaulelang == 'zh' else 'OK')

        # 添加“模型选择教程”按钮
        tutorial_button = QtWidgets.QPushButton(
            "点击查看模型选择教程" if config.defaulelang == 'zh' else "Model Selection Tutorial")
        msg_box.addButton(tutorial_button, QtWidgets.QMessageBox.ActionRole)

        # 显示消息框
        msg_box.exec()

        # 检查哪个按钮被点击
        if msg_box.clickedButton() == tutorial_button:
            tools.show_error("请参考项目文档" if config.defaulelang == 'zh' else "Please refer to the project documentation", False)

    def update_tips(self, text):
        if not self.update_btn:
            self.update_btn = QtWidgets.QPushButton()
            self.update_btn.setStyleSheet('color:#ffff00;border:0')
            self.update_btn.setCursor(Qt.PointingHandCursor)
            self.update_btn.clicked.connect(lambda: self.open_url('download'))
            self.main.container.addWidget(self.update_btn)
        self.update_btn.setText(text)

    # 关于页面
    def about(self):
        if config.INFO_WIN['win']:
            config.INFO_WIN['win'].show()
            return

        def open():
            from videotrans.component import InfoForm
            config.INFO_WIN['win'] = InfoForm()
            config.INFO_WIN['win'].show()

        QTimer.singleShot(50, open)

    def rephrase_fun(self,s,name):
        if s and name=='llm':
            self.main.rephrase_local.setChecked(False)
        elif s and name=='local':
            self.main.rephrase.setChecked(False)

    # 选中按钮时判断当前cuda是否可用
    def check_cuda(self, state):
        import torch
        res = state
        # 选中如果无效，则取消
        if state and not torch.cuda.is_available():
            tools.show_error(config.transobj['nocuda'], False)
            self.main.enable_cuda.setChecked(False)
            self.main.enable_cuda.setDisabled(True)
            res = False
        self.cfg['cuda'] = res

    # 启用标准模式
    def set_biaozhun(self):
        self.main.action_biaozhun.setChecked(True)
        self.main.splitter.setSizes([self.main.width - 300, 300])
        self.main.app_mode = 'biaozhun'
        self.main.show_tips.setText(
            "自定义各项配置，批量进行视频翻译。选择单个视频时，处理过程中可暂停编辑字幕" if config.defaulelang == 'zh' else 'Customize each configuration to batch video translation. When selecting a single video, you can pause to edit subtitles during processing.')
        self.main.startbtn.setText(config.transobj['kaishichuli'])
        self.main.action_tiquzimu.setChecked(False)

        # 仅保存视频行
        self.main.only_video.setDisabled(False)
        self.main.only_video.show()
        self.main.copysrt_rawvideo.hide()

        # 翻译
        self.main.label_9.show()
        self.main.translate_type.show()
        self.main.label_2.show()
        self.main.source_language.show()
        self.main.label_3.show()
        self.main.target_language.show()
        self.main.label.show()
        self.main.proxy.show()

        # 配音角色
        self.main.tts_text.show()
        self.main.tts_type.show()
        self.main.tts_type.setDisabled(False)
        self.main.label_4.show()
        self.main.voice_role.show()
        self.main.listen_btn.show()
        self.main.volume_label.show()
        self.main.volume_rate.show()
        self.main.volume_rate.setDisabled(False)
        self.main.pitch_label.show()
        self.main.pitch_rate.show()
        self.main.pitch_rate.setDisabled(False)

        # 语音识别行
        self.main.reglabel.show()
        self.main.recogn_type.show()
        self.main.model_name_help.show()
        self.main.model_name.show()
        self.main.split_label.show()
        self.main.split_type.show()
        self.main.subtitle_type.setCurrentIndex(1)
        self.main.subtitle_type.show()
        self.main.rephrase.show()
        self.main.remove_noise.show()

        # 字幕对齐行
        self.main.align_btn.show()
        self.main.voice_rate.show()
        self.main.label_6.show()
        self.main.voice_autorate.setChecked(True)
        self.main.voice_autorate.show()
        self.main.video_autorate.setChecked(True)
        self.main.video_autorate.show()
        self.main.is_separate.setDisabled(False)
        self.main.is_separate.setChecked(False)
        self.main.is_separate.show()
        self.main.enable_cuda.setChecked(False)
        self.main.label_cjklinenums.show()
        self.main.cjklinenums.show()
        self.main.label_othlinenums.show()
        self.main.othlinenums.show()
        if platform.system() != 'Darwin':
            self.main.enable_cuda.show()
        # 添加背景行
        self.main.addbackbtn.show()
        self.main.back_audio.show()
        self.main.is_loop_bgm.show()
        self.main.bgmvolume_label.show()
        self.main.bgmvolume.show()

    # 视频提取字幕并翻译，无需配音
    def set_tiquzimu(self):
        self.main.action_tiquzimu.setChecked(True)
        self.main.splitter.setSizes([self.main.width - 300, 300])
        self.main.app_mode = 'tiqu'
        self.main.show_tips.setText(config.transobj['tiquzimu'])
        self.main.startbtn.setText(config.transobj['kaishitiquhefanyi'])
        self.main.action_biaozhun.setChecked(False)

        # 仅保存视频行
        self.main.only_video.setChecked(False)
        self.main.only_video.hide()
        self.main.copysrt_rawvideo.show()

        # 翻译
        self.main.label_9.show()
        self.main.translate_type.show()
        self.main.label_2.show()
        self.main.source_language.show()
        self.main.label_3.show()
        self.main.target_language.show()
        self.main.label.show()
        self.main.proxy.show()

        # 配音角色
        self.main.tts_text.hide()
        self.main.tts_type.hide()
        self.main.label_4.hide()
        self.main.voice_role.hide()
        self.main.listen_btn.hide()
        self.main.volume_label.hide()
        self.main.volume_rate.hide()
        self.main.pitch_label.hide()
        self.main.pitch_rate.hide()

        # 语音识别行
        self.main.reglabel.show()
        self.main.recogn_type.show()
        self.main.model_name_help.show()
        self.main.model_name.show()
        self.main.split_label.show()
        self.main.split_type.show()
        self.main.subtitle_type.setCurrentIndex(1)
        self.main.subtitle_type.hide()
        self.main.rephrase.show()
        self.main.remove_noise.show()

        # 字幕对齐行
        self.main.align_btn.hide()
        self.main.label_6.hide()
        self.main.voice_rate.hide()
        self.main.voice_autorate.setChecked(True)
        self.main.voice_autorate.hide()
        self.main.video_autorate.setChecked(True)
        self.main.video_autorate.hide()

        self.main.is_separate.setChecked(False)
        self.main.is_separate.show()
        self.main.enable_cuda.setChecked(False)
        self.main.label_cjklinenums.hide()
        self.main.cjklinenums.hide()
        self.main.label_othlinenums.hide()
        self.main.othlinenums.hide()
        if platform.system() != 'Darwin':
            self.main.enable_cuda.show()
        # 添加背景行
        self.main.addbackbtn.hide()
        self.main.back_audio.hide()
        self.main.is_loop_bgm.hide()
        self.main.bgmvolume_label.hide()
        self.main.bgmvolume.hide()

    def source_language_change(self):
        from videotrans import translator
        langtext = self.main.source_language.currentText()
        langcode = translator.get_code(show_text=langtext)

    # 隐藏布局及其元素
    def hide_show_element(self, wrap_layout, show_status):
        def hide_recursive(layout, show_status):
            for i in range(layout.count()):
                item = layout.itemAt(i)
                if item.widget():
                    if not show_status:
                        item.widget().hide()
                    else:
                        item.widget().show()
                elif item.layout():
                    hide_recursive(item.layout(), show_status)

        hide_recursive(wrap_layout, show_status)

    def open_url(self, title):
        if title == 'online':
            self.about()
        else:
            tools.open_url(title=title)

    def remove_qsettings_data(self):
        try:
            Path(config.ROOT_DIR + "/videotrans/params.json").unlink(missing_ok=True)
            Path(config.ROOT_DIR + "/videotrans/cfg.json").unlink(missing_ok=True)
        except Exception:
            pass

    def clearcache(self):
        if config.defaulelang == 'zh':
            question = tools.show_popup('确认进行清理？', '清理后需要重启软件并重新填写设置菜单中各项配置信息')

        else:
            question = tools.show_popup('Confirm cleanup?', 'The software needs to be restarted after cleaning')

        if question == QtWidgets.QMessageBox.Yes:
            shutil.rmtree(config.TEMP_DIR, ignore_errors=True)
            shutil.rmtree(config.TEMP_HOME, ignore_errors=True)
            self.remove_qsettings_data()
            QtWidgets.QMessageBox.information(self.main,
                                              'Please restart the software' if config.defaulelang != 'zh' else '请重启软件',
                                              'Please restart the software' if config.defaulelang != 'zh' else '软件将自动关闭，请重新启动，设置中各项配置信息需重新填写')
            self.main.close()

    def get_mp4(self):
        # 如果有正在运行的任务，先停止并清理
        if config.current_status == 'ing':
            # 提示用户
            reply = QtWidgets.QMessageBox.question(
                self.main,
                '确认操作' if config.defaulelang == 'zh' else 'Confirm',
                '检测到有正在运行的任务，重新选择视频将停止当前任务并清空任务列表。是否继续？' if config.defaulelang == 'zh'
                else 'A task is currently running. Selecting new videos will stop the current task and clear the task list. Continue?',
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
            )
            if reply != QtWidgets.QMessageBox.Yes:
                return
            # 停止当前任务
            self.update_status('stop')

        # 完全清理旧的任务数据
        self.delete_process()  # 删除所有进度按钮
        self.queue_mp4 = []  # 清空视频队列
        self.obj_list = []  # 清空任务对象列表
        config.stoped_uuid_set.clear()  # 清空已停止任务集合

        # 确保状态正确（如果之前有错误任务导致状态异常）
        if config.current_status == 'ing':
            config.current_status = 'stop'

        if self.main.app_mode == 'tiqu':
            allowed_exts = config.VIDEO_EXTS + config.AUDIO_EXITS
        else:
            allowed_exts = config.VIDEO_EXTS
        format_str = " ".join(['*.' + f for f in allowed_exts])
        mp4_list = []
        if self.main.select_file_type.isChecked():
            """选择文件夹并添加到 selected_files 列表中"""
            folder_path = QtWidgets.QFileDialog.getExistingDirectory(
                self.main,
                "选择文件夹" if config.defaulelang else 'Select folder',
                config.params['last_opendir']
            )

            if not folder_path:
                return
            for root, _, files in os.walk(folder_path):
                for file in files:
                    if Path(file).suffix[1:].lower() in allowed_exts:
                        mp4_list.append(os.path.join(root, file).replace(os.sep, '/'))
            p = Path(folder_path)
            config.params['last_opendir'] = p.parent.as_posix()
            self.main.target_dir = config.params['last_opendir'] + f'/{p.name}_video_out'
            self.main.btn_save_dir.setToolTip(self.main.target_dir)
            self.update_save_dir_label(self.main.target_dir)
        else:
            fnames, _ = QtWidgets.QFileDialog.getOpenFileNames(self.main,
                                                               '选择一或多个文件' if config.defaulelang == 'zh' else "Select one or more files",
                                                               config.params['last_opendir'],
                                                               f'Files({format_str})')
            if len(fnames) < 1:
                return
            for (i, it) in enumerate(fnames):
                mp4_list.append(Path(it).as_posix())
            config.params['last_opendir'] = Path(mp4_list[0]).parent.resolve().as_posix()
            self.main.target_dir = config.params['last_opendir'] + f'/_video_out'
            self.main.btn_save_dir.setToolTip(self.main.target_dir)
            self.update_save_dir_label(self.main.target_dir)

        if len(mp4_list) > 0:
            self.main.source_mp4.setText(f'{len((mp4_list))} videos')
            self.queue_mp4 = mp4_list

    # 保存目录
    def get_save_dir(self):
        dirname = QtWidgets.QFileDialog.getExistingDirectory(self.main, config.transobj['selectsavedir'],
                                                             config.params['last_opendir'])
        dirname = Path(dirname).as_posix()
        self.main.target_dir = dirname
        self.main.btn_save_dir.setToolTip(self.main.target_dir)
        # 更新保存路径标签
        if dirname:
            self.update_save_dir_label(dirname)

    # 更新保存路径标签
    def update_save_dir_label(self, dirname):
        if not dirname or dirname == '.':
            self.main.save_dir_label.setText("📁 " + ("未选择" if config.defaulelang == 'zh' else "Not selected"))
            self.main.save_dir_label.setToolTip("")
        else:
            # 缩短显示的路径，只显示最后几个部分
            display_text = dirname
            if len(dirname) > 45:
                parts = dirname.split('/')
                if len(parts) > 3:
                    display_text = '.../' + '/'.join(parts[-2:])
                else:
                    display_text = '...' + dirname[-42:]
            self.main.save_dir_label.setText("📁 " + display_text)
            self.main.save_dir_label.setToolTip(f"{'点击打开文件夹' if config.defaulelang == 'zh' else 'Click to open folder'}:\n{dirname}")

    # 打开保存文件夹
    def open_save_dir(self):
        if not hasattr(self.main, 'target_dir') or not self.main.target_dir or self.main.target_dir == '.':
            tools.show_error("请先选择保存目录" if config.defaulelang == 'zh' else "Please select save directory first")
            return

        target_dir = Path(self.main.target_dir)
        # 如果目录不存在，尝试创建
        if not target_dir.exists():
            try:
                target_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                tools.show_error(f"{'无法创建目录' if config.defaulelang == 'zh' else 'Cannot create directory'}: {e}")
                return

        # 使用跨平台方式打开文件夹
        import platform
        import subprocess

        try:
            system = platform.system()
            if system == 'Windows':
                os.startfile(target_dir)
            elif system == 'Darwin':  # macOS
                subprocess.run(['open', target_dir])
            else:  # Linux
                subprocess.run(['xdg-open', target_dir])
        except Exception as e:
            tools.show_error(f"{'打开文件夹失败' if config.defaulelang == 'zh' else 'Failed to open folder'}: {e}")

    # 设置或删除代理
    def change_proxy(self, p):
        config.proxy = p.strip()
        try:
            if not config.proxy:
                # 删除代理
                tools.set_proxy('del')
            elif re.match(r'https?://(\d+\.){3}\d+:\d+', config.proxy):
                config.settings['proxy'] = config.proxy
        except Exception:
            pass

    # 核对代理填写
    def check_proxy(self):
        proxy = self.main.proxy.text().strip().replace('：', ':')
        if proxy:
            if not re.match(r'^(http|sock)', proxy, re.I):
                proxy = f'http://{proxy}'
            if not re.match(r'^(http|sock)(s|5)?://(\d+\.){3}\d+:\d+', proxy, re.I):
                question = tools.show_popup(
                    '请确认代理地址是否正确？' if config.defaulelang == 'zh' else 'Please make sure the proxy address is correct', """你填写的网络代理地址似乎不正确
        一般代理/vpn格式为 http://127.0.0.1:数字端口号 
        如果不知道什么是代理请勿随意填写
        ChatGPT等api地址请填写在菜单-设置-对应配置内。
        如果确认代理地址无误，请点击 Yes 继续执行""" if config.defaulelang == 'zh' else 'The network proxy address you fill in seems to be incorrect, the general proxy/vpn format is http://127.0.0.1:port, if you do not know what is the proxy please do not fill in arbitrarily, ChatGPT and other api address please fill in the menu - settings - corresponding configuration. If you confirm that the proxy address is correct, please click Yes to continue.')
                if question != QtWidgets.QMessageBox.Yes:
                    self.update_status('stop')
                    return False
        # 设置或删除代理
        config.proxy = proxy
        try:
            if config.proxy:
                # 设置代理
                tools.set_proxy(config.proxy)
                config.settings['proxy'] = config.proxy
            else:
                # 删除代理
                config.settings['proxy'] = ''
                tools.set_proxy('del')
            config.parse_init(config.settings)
        except:
            pass
        return True

    # 核对字幕
    def check_txt(self, txt=''):
        if txt and not re.search(r'\d{1,2}:\d{1,2}:\d{1,2}(.\d+)?\s*?-->\s*?\d{1,2}:\d{1,2}:\d{1,2}(.\d+)?', txt):
            tools.show_error(
                '字幕格式不正确，请重新导入字幕或删除已导入字幕' if config.defaulelang == 'zh' else 'Subtitle format is not correct, please re-import the subtitle or delete the imported subtitle.',
                False)
            return False
        return True

    # 如果选中了cuda，判断是否可用
    def cuda_isok(self):
        if not self.main.enable_cuda.isChecked() or platform.system() == 'Darwin':
            self.cfg['cuda'] = False
            return True

        import torch
        from videotrans import recognition
        if not torch.cuda.is_available():
            self.cfg['cuda'] = False
            tools.show_error(config.transobj["nocuda"], False)
            return False

        if self.main.recogn_type.currentIndex() == recognition.OPENAI_WHISPER:
            self.cfg['cuda'] = True
            return True
        allow = True
        try:
            from torch.backends import cudnn
            if not cudnn.is_available() or not cudnn.is_acceptable(torch.tensor(1.).cuda()):
                allow = False
        except:
            allow = False
        finally:
            if not allow:
                self.cfg['cuda'] = False
                self.main.enable_cuda.setChecked(False)
                tools.show_error(config.transobj["nocudnn"])
                return False
        self.cfg['cuda'] = True
        return True

    # 检测各个模式下参数是否设置正确
    def set_mode(self):
        subtitle_type = self.main.subtitle_type.currentIndex()
        voice_role = self.main.voice_role.currentText()
        self.cfg['copysrt_rawvideo'] = False
        if self.main.app_mode == 'tiqu' or (
                self.main.app_mode.startswith('biaozhun') and subtitle_type < 1 and voice_role in ('No', '', " ")):
            self.main.app_mode = 'tiqu'
            # 提取字幕模式，必须有视频、有原始语言，语音模型
            self.cfg['subtitle_type'] = 0
            self.cfg['voice_role'] = 'No'
            self.cfg['voice_rate'] = '+0%'
            self.cfg['voice_autorate'] = False
            self.cfg['back_audio'] = ''
            self.cfg['copysrt_rawvideo'] = self.main.copysrt_rawvideo.isChecked()

    # 导入背景声音
    def get_background(self):
        format_str = " ".join(['*.' + f for f in config.AUDIO_EXITS])
        fname, _ = QtWidgets.QFileDialog.getOpenFileName(self.main, 'Background music', config.params['last_opendir'],
                                                         f"Audio files({format_str})")
        if not fname:
            return
        fname = Path(fname).as_posix()
        self.main.back_audio.setText(fname)

    # 开启执行后，禁用按钮，停止或结束后，启用按钮
    def disabled_widget(self, type):
        self.main.clear_cache.setDisabled(type)
        self.main.volume_rate.setDisabled(type)
        self.main.pitch_rate.setDisabled(type)
        self.main.import_sub.setDisabled(type)
        self.main.btn_get_video.setDisabled(type)
        self.main.btn_save_dir.setDisabled(type)
        self.main.translate_type.setDisabled(type)
        self.main.proxy.setDisabled(type)
        self.main.source_language.setDisabled(type)
        self.main.target_language.setDisabled(type)
        self.main.tts_type.setDisabled(type)
        self.main.model_name.setDisabled(type)
        self.main.split_type.setDisabled(type)
        self.main.subtitle_type.setDisabled(type)
        self.main.enable_cuda.setDisabled(type)
        self.main.recogn_type.setDisabled(type)
        self.main.voice_autorate.setDisabled(type)
        self.main.video_autorate.setDisabled(type)
        self.main.voice_role.setDisabled(type)
        self.main.voice_rate.setDisabled(type)
        self.main.is_loop_bgm.setDisabled(type)
        self.main.only_video.setDisabled(True if self.main.app_mode in ['tiqu'] else type)
        self.main.is_separate.setDisabled(True if self.main.app_mode in ['tiqu'] else type)
        self.main.addbackbtn.setDisabled(True if self.main.app_mode in ['tiqu'] else type)
        self.main.back_audio.setReadOnly(True if self.main.app_mode in ['tiqu'] else type)

    # 0=整体识别模型
    # 1=均等分割模式
    def check_split_type(self, index):
        index = self.main.split_type.currentIndex()
        self.cfg['split_type'] = ['all', 'avg'][index]
        recogn_type = self.main.recogn_type.currentIndex()
        # 如果是均等分割，则阈值相关隐藏
        if recogn_type > 0:
            tools.hide_show_element(self.main.hfaster_layout, False)
            tools.hide_show_element(self.main.equal_split_layout, False)
        elif index == 1:
            tools.hide_show_element(self.main.equal_split_layout, True)
            tools.hide_show_element(self.main.hfaster_layout, False)
        else:
            tools.hide_show_element(self.main.equal_split_layout, False)

    # 试听配音
    def listen_voice_fun(self):
        import tempfile
        from videotrans import translator
        lang = translator.get_code(show_text=self.main.target_language.currentText())
        if not lang:
            return tools.show_error(
                '请先选择目标语言' if config.defaulelang == 'zh' else 'Please select the target language first', False)

        text = config.params.get(f'listen_text_{lang}')
        if not text:
            return tools.show_error('该角色不支持试听' if config.defaulelang == 'zh' else 'The voice is not support listen',
                                    False)
        role = self.main.voice_role.currentText()
        if not role or role == 'No':
            return tools.show_error(config.transobj['mustberole'], False)
        voice_dir = tempfile.gettempdir() + '/BDvideoTrans'
        if not Path(voice_dir).exists():
            Path(voice_dir).mkdir(parents=True, exist_ok=True)
        lujing_role = role.replace('/', '-')
        rate = int(self.main.voice_rate.value())
        if rate >= 0:
            rate = f"+{rate}%"
        else:
            rate = f"{rate}%"

        volume = int(self.main.volume_rate.value())
        volume = f'+{volume}%' if volume >= 0 else f'{volume}%'
        pitch = int(self.main.pitch_rate.value())
        pitch = f'+{pitch}Hz' if pitch >= 0 else f'{volume}Hz'

        voice_file = f"{voice_dir}/{self.main.tts_type.currentIndex()}-{lang}-{lujing_role}-{volume}-{pitch}.wav"

        obj = {
            "text": text,
            "rate": rate,
            "role": role,
            "filename": voice_file,
            "tts_type": self.main.tts_type.currentIndex(),
            "language": lang,
            "volume": volume,
            "pitch": pitch,
        }
        if role == 'clone':
            tools.show_error(
                '原音色克隆不可试听' if config.defaulelang == 'zh' else 'The original sound clone cannot be auditioned', False)
            return

        def feed(d):
            if d != "ok":
                tools.show_error(d)

        wk = ListenVoice(parent=self.main, queue_tts=[obj], language=lang, tts_type=obj['tts_type'])
        wk.uito.connect(feed)
        wk.start()

    # 角色改变时 显示试听按钮
    def show_listen_btn(self, role):
        from videotrans import tts
        tts_type = self.main.tts_type.currentIndex()
        voice_role = self.main.voice_role.currentText()
        if role == 'No' or (tts_type == tts.CLONE_VOICE_TTS and voice_role == 'clone'):
            self.main.listen_btn.hide()
            return
        if self.main.app_mode in ['biaozhun']:
            self.main.listen_btn.show()
            self.main.listen_btn.setDisabled(False)

    # 判断文件路径是否正确
    def url_right(self):
        if sys.platform != 'win32':
            return True
        for vurl in self.queue_mp4:
            if re.search(r'[:\?\*<>\|\"]', vurl[4:]):
                return tools.show_error(
                    '视频所在路径和视频名字中不可含有  :  * ? < > | "  符号，请修正 ' if config.defaulelang == 'zh' else 'The path and name of the video must not contain the  : * ? < > | "  symbols, please revise. ',
                    False)
            if len(vurl) > 255:
                return tools.show_error(
                    f'视频路径总长度超过255个字符，处理中可能会出错，请改短视频文件名，并移动到浅层目录下url={vurl}' if config.defaulelang == 'zh' else f'The total length of the video path is more than 255 characters, there may be an error in processing, please change the short video file name and move it to a shallow directoryurl={vurl}',
                    False)
        return True

    # 如果存在音频则设为提取
    # 如果有同名则停止
    def check_name(self):
        if self.main.app_mode != 'tiqu':
            for it in self.queue_mp4:
                if Path(it).suffix.lower() in config.AUDIO_EXITS:
                    self.main.app_mode = 'tiqu'
                    self.cfg['is_separate'] = False
                    break

        if len(self.queue_mp4) > 1:
            same_name = {}
            for it in self.queue_mp4:
                p = Path(it)
                stem = p.stem
                if stem in same_name:
                    same_name[stem].append(p.name)
                else:
                    same_name[stem] = [p.name]
            msg = ''
            for it in same_name.values():
                if len(it) > 1:
                    msg += ",".join(it)
            if msg:
                tools.show_error(
                    f'不可含有名字相同但后缀不同的文件，会导致混淆，请修改 {msg} ' if config.defaulelang == 'zh' else f'Do not include files with the same name but different extensions, this can lead to confusion, please modify {msg} ',
                    False)
                return False
        return True

    def clear_target_subtitle(self):
        """安全地清除布局中的所有项目，保留布局本身。"""
        if self.removing_layout or not self.scroll_area or not self.scroll_area_after or not self.scroll_area_search:
            return
        self.removing_layout = True

        def clear_and_delete_scroll_area(scroll_area):
            if scroll_area is None:
                return
            widget = scroll_area.takeWidget()
            if widget:
                if widget.layout():
                    delete_layout_and_children(widget.layout())
            if scroll_area.parent() and isinstance(scroll_area.parent(), QtWidgets.QLayout):
                scroll_area.parent().removeWidget(scroll_area)

            scroll_area.deleteLater()

        def delete_layout_and_children(layout):
            if layout is None:
                return
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget:
                    widget.deleteLater()
                elif item.layout():
                    delete_layout_and_children(item.layout())
                del item

        try:
            clear_and_delete_scroll_area(self.scroll_area)
            delete_layout_and_children(self.scroll_area_after)
            delete_layout_and_children(self.scroll_area_search)
        except Exception as e:
            print(e)
        self.scroll_area = None
        self.scroll_area_after = None
        self.scroll_area_search = None
        self.removing_layout = False

    def get_target_subtitle(self):
        srts = self.extract_subtitle_data_from_area(self.main.target_subtitle_area)
        return '\n\n'.join(srts)

    def extract_subtitle_data_from_area(self, target_layout):
        def find_box(layout):
            if layout is None:
                return None
            for i in range(layout.count()):
                item = layout.itemAt(i)
                if item is None:
                    continue
                widget = item.widget()
                if isinstance(widget, QtWidgets.QScrollArea):
                    box = widget.widget()
                    if isinstance(box, QtWidgets.QWidget) and box.objectName() == 'box_name':
                        return box
                elif item.layout():
                    box = find_box(item.layout())
                    if box:
                        return box
            return None

        box = find_box(target_layout)
        if box is None:
            return []  # 没有找到box

        return self.extract_subtitle_data(box)

    def extract_subtitle_data(self, box):
        data = []
        layout = box.layout()
        if layout is None:
            return data
        num = 1
        for item in layout.children():
            if isinstance(item, QtWidgets.QVBoxLayout):
                for i in range(item.count()):
                    child = item.itemAt(i)
                    if child is None:
                        continue
                    widget = child.widget()
                    if isinstance(widget, QtWidgets.QLineEdit):
                        line_time_text = widget.text()
                    elif isinstance(widget, QtWidgets.QPlainTextEdit):
                        line_edit_text = widget.toPlainText()
                        data.append(f'{num}\n{line_time_text}\n{line_edit_text}')
                        num += 1
        return data

    def replace_text(self, s_text='', t_text=''):
        if not s_text:
            return tools.show_error(
                "必须输入要被替换的原始文字" if config.defaulelang == 'zh' else 'The original text to be replaced must be entered',
                False)

        top_layout = self.scroll_area.widget().layout()
        if top_layout is None:
            return

        for i in range(top_layout.count()):
            item = top_layout.itemAt(i)
            if not item:
                continue

            if not isinstance(item, QtWidgets.QLayoutItem):
                continue
            layout = item.layout()
            if not layout:
                continue
            for j in range(layout.count()):
                child = layout.itemAt(j)
                if not child or not isinstance(child, QtWidgets.QWidgetItem):
                    continue
                widget = child.widget()
                if not isinstance(widget, QtWidgets.QPlainTextEdit):
                    continue
                line_edit_text = widget.toPlainText()

                if line_edit_text.lower().find(s_text.lower()) > -1:
                    new_text = line_edit_text.replace(s_text, t_text)
                    widget.setPlainText(new_text)

    def show_target_edit(self, srt_str):
        def get_checked_boxes(widget):
            checked_boxes = []
            for child in widget.children():
                if isinstance(child, QtWidgets.QCheckBox) and child.isChecked():
                    checked_boxes.append(child.objectName())
                else:
                    checked_boxes.extend(get_checked_boxes(child))
            return checked_boxes

        def save():
            role = select_role.currentText()
            # 初始化一个列表，用于存放所有选中 checkbox 的名字
            checked_checkbox_names = get_checked_boxes(box)
            default_role = self.cfg.get('voice_role', 'No')

            if len(checked_checkbox_names) < 1:
                return tools.show_error("至少要选择一条字幕" if config.defaulelang == 'zh' else 'Choose at least one subtitle',
                                        False)

            for n in checked_checkbox_names:
                _, line = n.split('_')
                # 设置labe为角色名
                ck = box.findChild(QtWidgets.QCheckBox, n)
                ck.setText(default_role if role in ['No', 'no', '-'] else role)
                ck.setChecked(False)
                config.line_roles[line] = default_role if role in ['No', 'no', '-'] else role

        box = QtWidgets.QWidget()
        box.setObjectName('box_name')
        box.setLayout(QtWidgets.QVBoxLayout())

        #  获取字幕
        srt_json = tools.get_subtitle_from_srt(srt_str, is_file=False)
        for it in srt_json:
            # 创建新水平布局
            v_layout = QtWidgets.QVBoxLayout()
            v_layout.setObjectName(f'hlayout_{it["line"]}')
            h_layout = QtWidgets.QHBoxLayout()
            label = QtWidgets.QLabel()
            label.setText(f'{it["line"]}')
            check = QtWidgets.QCheckBox()
            check.setToolTip(
                "选中后可在底部单独设置配音角色" if config.defaulelang == 'zh' else "Check to set the voice role separately at the bottom")
            check.setText(
                config.line_roles[f'{it["line"]}'] if f'{it["line"]}' in config.line_roles else
                self.cfg.get('voice_role', 'No'))
            check.setObjectName(f'check_{it["line"]}')
            # 创建并配置 QLineEdit
            line_time = QtWidgets.QLineEdit()
            line_time.setObjectName(f'time_{it["line"]}')
            line_time.setText(f'{it["time"]}')

            line_edit = QtWidgets.QPlainTextEdit()
            line_edit.setObjectName(f'text_{it["line"]}')
            line_edit.setPlainText(f'{it["text"]}')
            # 将标签和编辑线添加到水平布局
            h_layout.addWidget(label)
            h_layout.addWidget(check)
            h_layout.addStretch()
            v_layout.addLayout(h_layout)
            v_layout.addWidget(line_time)
            v_layout.addWidget(line_edit)
            box.layout().addLayout(v_layout)
        box.layout().setAlignment(Qt.AlignmentFlag.AlignTop)

        select_role = QtWidgets.QComboBox()
        select_role.addItems(self.main.current_rolelist)
        select_role.setFixedHeight(35)

        apply_role_btn = QtWidgets.QPushButton()
        apply_role_btn.setMinimumSize(80, 30)
        apply_role_btn.setText('应用' if config.defaulelang == 'zh' else 'Apply')
        apply_role_btn.clicked.connect(save)

        if self.cfg.get('voice_role', '-') in ['-', 'No', 'clone']:
            select_role.setDisabled(True)
            apply_role_btn.setDisabled(True)
        label_role = QtWidgets.QLabel()
        label_role.setText('设置角色' if config.defaulelang == 'zh' else 'Select Role')

        source_text = QtWidgets.QLineEdit()
        source_text.setPlaceholderText('原文字' if config.defaulelang == 'zh' else 'Original text')
        source_text.setMaximumWidth(200)

        tips_text = QtWidgets.QLabel()
        tips_text.setText('替换为' if config.defaulelang == 'zh' else 'Replace')

        target_text = QtWidgets.QLineEdit()
        target_text.setPlaceholderText('目标文字' if config.defaulelang == 'zh' else 'Original text')
        target_text.setMaximumWidth(200)

        replace_btn = QtWidgets.QPushButton()
        replace_btn.setMinimumSize(80, 30)
        replace_btn.setText('替换' if config.defaulelang == 'zh' else 'Replace')
        replace_btn.clicked.connect(lambda: self.replace_text(source_text.text(), target_text.text()))

        self.scroll_area_search = QtWidgets.QHBoxLayout()
        self.scroll_area_search.addWidget(source_text)  # Give more space to LineEdits
        self.scroll_area_search.addWidget(tips_text)
        self.scroll_area_search.addWidget(target_text)  # Give more space to LineEdits
        self.scroll_area_search.addWidget(replace_btn)  # Align to right and less space to button
        self.scroll_area_search.addStretch()

        self.scroll_area_after = QtWidgets.QHBoxLayout()
        self.scroll_area_after.addWidget(label_role)
        self.scroll_area_after.addWidget(select_role)
        self.scroll_area_after.addWidget(apply_role_btn)

        self.scroll_area = QtWidgets.QScrollArea()
        self.scroll_area.setWidget(box)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setAlignment(Qt.AlignmentFlag.AlignTop)

        # 将 QScrollArea 添加到主窗口的 layout
        self.main.target_subtitle_area.addWidget(self.scroll_area)
        self.main.target_subtitle_area.addLayout(self.scroll_area_search)
        self.main.target_subtitle_area.addLayout(self.scroll_area_after)
