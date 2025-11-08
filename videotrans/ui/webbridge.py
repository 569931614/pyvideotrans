from __future__ import annotations

import os
from typing import List, Dict, Any

from PySide6.QtCore import QObject, Signal, Slot
from PySide6.QtWidgets import QFileDialog, QMessageBox

from videotrans.configure import config
from videotrans import recognition, tts
from videotrans.translator import TRANSLASTE_NAME_LIST
from videotrans.util import tools


class WebBridge(QObject):
    """Bridge object exposed to Web via QWebChannel.

    Methods decorated with @Slot can be invoked from JS.
    Use simple types (str, int, float, bool, list, dict) for IPC.
    """

    # Signals back to JS
    notify = Signal(str, dict)

    def __init__(self, main_window):
        super().__init__()
        self._main_window = main_window

    # ========== Utility ==========
    def _ensure_main_action(self):
        if not getattr(self._main_window, "win_action", None):
            raise RuntimeError("Main window action not ready")
        return self._main_window.win_action

    def _get_voice_roles(self) -> List[Dict[str, str]]:
        """Get voice roles based on current TTS type and target language."""
        import re

        tts_type = config.params.get('tts_type', 0)
        target_language = config.params.get('target_language', '')

        roles = []

        try:
            if tts_type == tts.GOOGLE_TTS:
                roles = ['gtts']
            elif tts_type == tts.OPENAI_TTS:
                rolelist = config.params.get('openaitts_role', '')
                roles = rolelist.split(',') if rolelist else []
            elif tts_type == tts.QWEN_TTS:
                rolelist = config.params.get('qwentts_role', '')
                roles = rolelist.split(',') if rolelist else []
            elif tts_type == tts.GEMINI_TTS:
                rolelist = config.params.get('gemini_ttsrole', '')
                roles = rolelist.split(',') if rolelist else []
            elif tts_type == tts.ELEVENLABS_TTS:
                roles = config.params.get('elevenlabstts_role', [])
                if not roles:
                    roles = tools.get_elevenlabs_role()
            elif tts_type == tts.CHATTTS:
                config.ChatTTS_voicelist = re.split(r'[,，]', config.settings.get('chattts_voice', ''))
                roles = list(config.ChatTTS_voicelist)
            elif tts_type == tts.TTS_API:
                roles = config.params.get('ttsapi_voice_role', '').strip().split(',')
            elif tts_type == tts.GPTSOVITS_TTS:
                rolelist = tools.get_gptsovits_role()
                roles = list(rolelist.keys()) if rolelist else ['GPT-SoVITS']
            elif tts_type == tts.CHATTERBOX_TTS:
                rolelist = tools.get_chatterbox_role()
                roles = rolelist if rolelist else ['chatterbox']
            elif tts_type == tts.COSYVOICE_TTS:
                rolelist = tools.get_cosyvoice_role()
                roles = list(rolelist.keys()) if rolelist else ['clone']
            elif tts_type == tts.FISHTTS:
                rolelist = tools.get_fishtts_role()
                roles = list(rolelist.keys()) if rolelist else ['FishTTS']
            elif tts_type == tts.F5_TTS:
                rolelist = tools.get_f5tts_role()
                roles = list(rolelist.keys()) if rolelist else ['F5-TTS']
            elif tts_type == tts.CLONE_VOICE_TTS:
                roles = config.params.get("clone_voicelist", [])
            elif tts_type in [tts.EDGE_TTS, tts.AZURE_TTS, tts.VOLCENGINE_TTS, tts.AI302_TTS, tts.KOKORO_TTS]:
                # These TTS types require target language
                if not target_language or target_language == '-':
                    return [{"value": "请先选择目标语言", "label": "请先选择目标语言"}]

                # Convert language name to language code
                from videotrans import translator
                code = translator.get_code(show_text=target_language)
                if not code or code == '-':
                    return [{"value": "No", "label": "No"}]

                # Get role list based on TTS type
                if tts_type == tts.EDGE_TTS:
                    show_rolelist = tools.get_edge_rolelist()
                elif tts_type == tts.KOKORO_TTS:
                    show_rolelist = tools.get_kokoro_rolelist()
                elif tts_type == tts.AI302_TTS:
                    show_rolelist = tools.get_302ai()
                elif tts_type == tts.VOLCENGINE_TTS:
                    show_rolelist = tools.get_volcenginetts_rolelist()
                else:  # AZURE_TTS
                    show_rolelist = tools.get_azure_rolelist()

                if not show_rolelist:
                    return [{"value": "No", "label": "No"}]

                # Get language prefix
                vt = code.split('-')[0] if code != 'yue' else "zh"

                if vt not in show_rolelist:
                    return [{"value": "No", "label": "No"}]

                roles = show_rolelist[vt]
                # Remove 'No' from the list if it exists
                if 'No' in roles:
                    roles = [r for r in roles if r != 'No']
            else:
                roles = ['No']
        except Exception as e:
            print(f"Error getting voice roles: {e}")
            roles = ['No']

        # Convert to list of dicts and add 'No' at the end if not already present
        result = [{"value": r, "label": r} for r in roles if r and r != 'No']
        result.append({"value": "No", "label": "No"})

        return result

    # ========== Slots for JS ==========
    @Slot(result=dict)
    def getInitState(self) -> Dict[str, Any]:
        """Return initial state for Web UI to render controls."""
        try:
            state = {
                "version": getattr(self._main_window, "rawtitle", "BDvideoTrans"),
                "sourceLanguages": self._main_window.languagename,
                "targetLanguages": ["-"] + self._main_window.languagename[:-1],
                "translateTypes": TRANSLASTE_NAME_LIST,
                "targetDir": config.params.get("target_dir", ""),
                "proxy": config.proxy,
            }
            return state
        except Exception as e:
            return {"error": str(e)}

    @Slot(result=dict)
    def getOptions(self) -> Dict[str, Any]:
        """Return all major option lists and current selections for the Web UI."""
        try:
            langs = [{"value": l, "label": l} for l in self._main_window.languagename]
            def with_index(items: List[str]) -> List[Dict[str, Any]]:
                return [{"value": i, "label": s} for i, s in enumerate(items)]

            # Helper function to safely parse numeric values with units
            def safe_parse_int(value, default=0):
                """Safely parse int from value, removing common suffixes"""
                try:
                    if value is None:
                        return default
                    val_str = str(value).replace('%', '').replace('Hz', '').strip()
                    return int(val_str) if val_str else default
                except (ValueError, AttributeError):
                    return default

            # Get voice roles based on current TTS type and target language
            try:
                voice_roles = self._get_voice_roles()
            except Exception as e:
                print(f"Error getting voice roles: {e}")
                import traceback
                traceback.print_exc()
                voice_roles = [{"value": "No", "label": "No"}]

            opts: Dict[str, Any] = {
                "languages": langs,
                "translateTypes": with_index(TRANSLASTE_NAME_LIST),
                "ttsTypes": with_index(tts.TTS_NAME_LIST),
                "recognitionTypes": with_index(recognition.RECOGN_NAME_LIST),
                "whisperModels": [{"value": m, "label": m} for m in config.WHISPER_MODEL_LIST],
                "deepgramModels": [{"value": m, "label": m} for m in getattr(config, 'DEEPGRAM_MODEL', [])],
                "funasrModels": [{"value": m, "label": m} for m in getattr(config, 'FUNASR_MODEL', [])],
                "subtitleTypes": with_index([
                    config.transobj.get('nosubtitle','No Subtitle'),
                    config.transobj.get('embedsubtitle','Embed Subtitle'),
                    config.transobj.get('softsubtitle','Soft Subtitle'),
                    config.transobj.get('embedsubtitle2','Embed Subtitle2'),
                    config.transobj.get('softsubtitle2','Soft Subtitle2'),
                ]),
                "voiceRoles": voice_roles,
                "splitTypes": {
                    "all": config.transobj.get('whisper_type_all','all'),
                    "avg": config.transobj.get('whisper_type_avg','avg')
                },
                "selected": {
                    "translate_type": config.params.get('translate_type', 0),
                    "source_language": config.params.get('source_language', ''),
                    "target_language": config.params.get('target_language', ''),
                    "tts_type": config.params.get('tts_type', 0),
                    "voice_role": config.params.get('voice_role',''),
                    "recogn_type": config.params.get('recogn_type', 0),
                    "model_name": config.params.get('model_name',''),
                    "split_type": config.params.get('split_type','all'),
                    "subtitle_type": int(config.params.get('subtitle_type', 0)),
                    "voice_rate": safe_parse_int(config.params.get('voice_rate', '0')),
                    "volume": safe_parse_int(config.params.get('volume', 0)),
                    "pitch": safe_parse_int(config.params.get('pitch', '0')),
                    "voice_autorate": bool(config.params.get('voice_autorate')),
                    "video_autorate": bool(config.params.get('video_autorate')),
                    "enable_cuda": bool(config.params.get('cuda')),
                    "enable_hearsight": bool(config.params.get('enable_hearsight', False)),
                    "aisendsrt": bool(config.settings.get('aisendsrt', False)),
                    "remove_noise": bool(config.params.get('remove_noise', False)),
                }
            }
            return opts
        except Exception as e:
            print(f"Error in getOptions: {e}")
            import traceback
            traceback.print_exc()
            return {"error": str(e)}

    @Slot(result=dict)
    def selectVideo(self) -> Dict[str, Any]:
        """Open file dialog to select videos; return file paths list and target_dir."""
        try:
            files, _ = QFileDialog.getOpenFileNames(
                self._main_window,
                "选择要处理的视频",
                config.params.get("target_dir", ""),
                "Video Files (*.mp4 *.mov *.mkv *.avi *.flv);;All Files (*)",
            )
            if files:
                # 只有当用户还没有明确选择保存目录时，才使用视频所在目录作为默认值
                # 如果用户已经通过"选择保存目录"按钮选择了目录，则不覆盖
                current_target_dir = config.params.get("target_dir", "")
                if not current_target_dir or not os.path.isdir(current_target_dir):
                    # 没有保存目录或目录无效，使用视频所在目录作为默认值
                    config.params["target_dir"] = os.path.dirname(files[0])
                # Set to queue_mp4 for processing
                self._set_video_queue(files)

            # 返回文件列表和当前的保存目录
            return {
                "files": files,
                "target_dir": config.params.get("target_dir", "")
            }
        except Exception as e:
            QMessageBox.critical(self._main_window, "错误", f"选择视频失败：\n{e}")
            return {"files": [], "target_dir": ""}

    @Slot(list)
    def setVideoQueue(self, files: List[str]) -> None:
        """Set video queue from JavaScript."""
        self._set_video_queue(files)

    def _set_video_queue(self, files: List[str]) -> None:
        """Internal method to set video queue."""
        win_action = self._ensure_main_action()
        win_action.queue_mp4 = []
        for file in files:
            if os.path.exists(file):
                win_action.queue_mp4.append(file)
        print(f"Video queue set: {len(win_action.queue_mp4)} files")

    @Slot(result=str)
    def selectSaveDir(self) -> str:
        """Choose output directory; update config and return path."""
        try:
            directory = QFileDialog.getExistingDirectory(
                self._main_window, "选择保存目录", config.params.get("target_dir", "")
            )
            if directory:
                config.params["target_dir"] = directory
            return directory or ""
        except Exception as e:
            QMessageBox.critical(self._main_window, "错误", f"选择目录失败：\n{e}")
            return ""

    @Slot(str)
    def setProxy(self, proxy: str) -> None:
        config.proxy = proxy or ""
        self.notify.emit("proxyChanged", {"proxy": config.proxy})

    @Slot(dict)
    def setParams(self, params: Dict[str, Any]) -> None:
        """Batch-update a subset of params from Web UI."""
        if not isinstance(params, dict):
            return
        try:
            for key, value in params.items():
                # allowlist minimal keys for safety
                if key == 'proxy':
                    config.proxy = value or ''
                    continue
                if key == 'aisendsrt':
                    config.settings['aisendsrt'] = bool(value)
                    continue
                if key == 'voice_rate':
                    try:
                        # Remove % suffix if present, then convert to int
                        val_str = str(value).replace('%', '').strip()
                        config.params['voice_rate'] = f"{int(val_str)}%"
                    except Exception as e:
                        print(f"Warning: Could not parse voice_rate value '{value}': {e}")
                        config.params['voice_rate'] = "0%"
                    continue
                if key == 'pitch':
                    try:
                        # Remove Hz suffix if present, then convert to int
                        val_str = str(value).replace('Hz', '').strip()
                        config.params['pitch'] = f"{int(val_str)}Hz"
                    except Exception as e:
                        print(f"Warning: Could not parse pitch value '{value}': {e}")
                        config.params['pitch'] = "0Hz"
                    continue
                # direct mappings
                if key in {
                    "translate_type","source_language","target_language","subtitle_type",
                    "tts_type","voice_role","recogn_type","model_name","split_type",
                    "volume","voice_autorate","video_autorate","cuda","enable_hearsight",
                    "remove_noise","trim_start","trim_end"
                }:
                    config.params[key] = value
                    # Debug log for preprocessing
                    if key in ('trim_start', 'trim_end'):
                        print(f"[DEBUG] {key} set to: {value}")
                        config.logger.info(f"[DEBUG] {key} set to: {value}")
                    # Debug log for enable_hearsight
                    if key == 'enable_hearsight':
                        print(f"[DEBUG] enable_hearsight set to: {value}")
                        config.logger.info(f"[DEBUG] enable_hearsight set to: {value}")
            self.notify.emit("paramsUpdated", {"params": params})
        except Exception as e:
            QMessageBox.critical(self._main_window, "错误", f"更新参数失败：\n{e}")

    @Slot(result=dict)
    def startTranslate(self) -> dict:
        """Start translation process using task queue system.

        Returns:
            dict: {'success': bool, 'task_uuids': [{'path': str, 'uuid': str}]}
        """
        # 创建调试日志文件
        import sys
        debug_log_path = config.ROOT_DIR + "/debug_startTranslate.log"
        try:
            debug_log = open(debug_log_path, 'w', encoding='utf-8')
            debug_log.write("=== startTranslate called ===\n")
            debug_log.flush()
        except:
            debug_log = None

        def log(msg):
            print(msg)
            sys.stdout.flush()
            if debug_log:
                debug_log.write(msg + "\n")
                debug_log.flush()

        try:
            from videotrans.util import tools
            from videotrans.task.trans_create import TransCreate
            from pathlib import Path

            log("[DEBUG] Imports successful")
            win_action = self._ensure_main_action()
            log("[DEBUG] win_action obtained")

            # Check if already running
            log(f"[DEBUG] Checking current_status: {config.current_status}")
            if config.current_status == 'ing':
                log("[DEBUG] Task already running")
                QMessageBox.warning(self._main_window, "提示", "任务正在执行中...")
                return {'success': False, 'task_uuids': []}

            # Check if has videos
            log(f"[DEBUG] Checking queue_mp4 length: {len(win_action.queue_mp4)}")
            if len(win_action.queue_mp4) < 1:
                log("[DEBUG] No videos selected")
                QMessageBox.warning(self._main_window, "错误",
                    "必须选择视频文件" if config.defaulelang == 'zh' else "Video file must be selected")
                return {'success': False, 'task_uuids': []}

            # 在读取参数前，先输出config.params中的预处理参数
            log(f"[DEBUG] config.params before reading:")
            log(f"  trim_start from config.params: {config.params.get('trim_start', 'NOT_FOUND')}")
            log(f"  trim_end from config.params: {config.params.get('trim_end', 'NOT_FOUND')}")

            # Build base config from params
            base_cfg = {
                'translate_type': config.params.get('translate_type', 0),
                'source_language': config.params.get('source_language', ''),
                'target_language': config.params.get('target_language', '-'),
                'tts_type': config.params.get('tts_type', 0),
                'voice_role': config.params.get('voice_role', 'No'),
                'volume': config.params.get('volume', '+0%'),
                'pitch': config.params.get('pitch', '+0Hz'),
                'recogn_type': config.params.get('recogn_type', 0),
                'model_name': config.params.get('model_name', 'base'),
                'split_type': config.params.get('split_type', 'all'),
                'subtitle_type': int(config.params.get('subtitle_type', 0)),
                'voice_rate': config.params.get('voice_rate', '+0%'),
                'voice_autorate': bool(config.params.get('voice_autorate', False)),
                'video_autorate': bool(config.params.get('video_autorate', False)),
                'is_separate': False,
                'cuda': bool(config.params.get('cuda', False)),
                'back_audio': '',
                'only_video': False,
                'clear_cache': True,
                'remove_noise': bool(config.params.get('remove_noise', False)),
                # 视频预处理参数
                'trim_start': float(config.params.get('trim_start', 0)),
                'trim_end': float(config.params.get('trim_end', 0)),
            }

            log(f"[DEBUG] base_cfg after building:")
            log(f"  trim_start in base_cfg: {base_cfg.get('trim_start')}")
            log(f"  trim_end in base_cfg: {base_cfg.get('trim_end')}")
            log(f"Starting translation with base config: {base_cfg}")
            log(f"Queue: {len(win_action.queue_mp4)} videos")

            # Store task UUID mapping for frontend
            task_uuids = []
            log(f"[DEBUG] task_uuids list created")

            # Create and add tasks to queue for each video
            log(f"[DEBUG] Starting to process {len(win_action.queue_mp4)} videos")
            for video_path in win_action.queue_mp4:
                log(f"[DEBUG] Processing video: {video_path}")
                try:
                    # Create obj using format_video
                    log(f"[DEBUG] Calling tools.format_video...")
                    obj = tools.format_video(video_path, config.params.get('target_dir', ''))
                    log(f"[DEBUG] format_video returned UUID: {obj.get('uuid', 'NO UUID')}")
                    obj['target_dir'] = config.params.get('target_dir', '') + f'/{obj["uuid"]}'
                    obj['cache_folder'] = config.TEMP_DIR + f'/{obj["uuid"]}'

                    # Create directories
                    log(f"[DEBUG] Creating directories...")
                    Path(obj['target_dir']).mkdir(parents=True, exist_ok=True)

                    # Merge obj into cfg
                    log(f"[DEBUG] Merging config...")
                    cfg = base_cfg.copy()
                    cfg.update(obj)

                    # Create task (only pass cfg)
                    log(f"[DEBUG] Creating TransCreate task...")
                    task = TransCreate(cfg=cfg)

                    # Add to prepare queue
                    log(f"[DEBUG] Adding task to prepare_queue...")
                    config.prepare_queue.append(task)
                    log(f"Task added to queue: {video_path}")

                    # Store UUID for frontend
                    log(f"[DEBUG] Storing UUID for frontend: {obj['uuid']}")
                    log(f"[DEBUG] task_uuids before append: {task_uuids}")
                    task_uuids.append({
                        'path': video_path,
                        'uuid': obj['uuid']
                    })
                    log(f"[DEBUG] task_uuids after append: {task_uuids}")

                    # Set initial status
                    log(f"[DEBUG] Setting initial status...")
                    tools.set_process(
                        text=f"在队列中等待 No.{len(config.prepare_queue)}",
                        uuid=obj['uuid']
                    )
                    log(f"[DEBUG] Task processing completed for {video_path}")

                except Exception as e:
                    log(f"[ERROR] Failed to create task for {video_path}: {e}")
                    import traceback
                    traceback.print_exc()
                    if debug_log:
                        traceback.print_exc(file=debug_log)
                        debug_log.flush()

            # Update status
            config.current_status = 'ing'

            # Store task UUIDs for frontend retrieval
            config.params['_current_task_uuids'] = task_uuids

            log(f"[DEBUG] startTranslate completed successfully")
            log(f"[DEBUG] Returning {len(task_uuids)} task UUIDs")
            log(f"[DEBUG] task_uuids content: {task_uuids}")
            log(f"[DEBUG] prepare_queue length: {len(config.prepare_queue)}")

            QMessageBox.information(self._main_window, "提示",
                f"已添加 {len(win_action.queue_mp4)} 个任务到处理队列")

            result = {'success': True, 'task_uuids': task_uuids}
            log(f"[DEBUG] Returning result: {result}")

            if debug_log:
                debug_log.write("=== startTranslate completed ===\n")
                debug_log.close()

            return result

        except Exception as e:
            log(f"[ERROR] Error in startTranslate: {e}")
            import traceback
            traceback.print_exc()
            if debug_log:
                traceback.print_exc(file=debug_log)
                debug_log.close()
            QMessageBox.critical(self._main_window, "错误", f"启动处理失败：\n{e}")
            return {'success': False, 'task_uuids': []}

    @Slot(result=dict)
    def getTaskProgress(self) -> Dict[str, Any]:
        """Get progress updates for all tasks in queue.

        Returns a dict mapping uuid -> latest progress info.
        Progress info includes: text, type, percent, status
        """
        try:
            from videotrans.configure import config
            result = {}

            # Iterate through all uuid queues and get the latest message
            for uuid in list(config.uuid_logs_queue.keys()):
                queue_obj = config.uuid_logs_queue.get(uuid)
                if queue_obj is None or not hasattr(queue_obj, 'queue'):
                    continue

                # Access queue items without removing them
                # Get the most recent message
                try:
                    # queue.queue is a deque, we can access it directly
                    messages = list(queue_obj.queue)
                    if not messages:
                        continue

                    # Use the latest message
                    latest = messages[-1]

                    # Determine status from message type
                    msg_type = latest.get('type', 'logs')
                    status = 'processing'
                    percent = 0
                    text = latest.get('text', '')

                    if msg_type == 'succeed':
                        status = 'completed'
                        percent = 100
                    elif msg_type == 'error':
                        status = 'error'
                    elif msg_type == 'stop':
                        status = 'stopped'
                    elif msg_type == 'set_precent':
                        status = 'processing'
                        # Extract percent from text format: "状态文本 时间???百分比"
                        try:
                            import re
                            # Look for pattern like "5s???10" or "???10"
                            match = re.search(r'\?\?\?(\d+)', text)
                            if match:
                                percent = min(100, max(0, int(match.group(1))))
                            else:
                                # Fallback: try to find any number followed by optional %
                                match = re.search(r'(\d+)%?', text)
                                if match:
                                    percent = min(100, max(0, int(match.group(1))))
                        except Exception as e:
                            print(f"Error parsing percent from '{text}': {e}")
                            pass
                    else:
                        # For other message types, try to extract percent if available
                        try:
                            import re
                            match = re.search(r'(\d+)%', text)
                            if match:
                                percent = min(100, max(0, int(match.group(1))))
                        except:
                            pass

                    result[uuid] = {
                        'text': text,
                        'type': msg_type,
                        'status': status,
                        'percent': percent
                    }

                except Exception as e:
                    print(f"Error reading queue for {uuid}: {e}")
                    continue

            return result
        except Exception as e:
            print(f"Error in getTaskProgress: {e}")
            import traceback
            traceback.print_exc()
            return {}

    @Slot()
    def resetStatus(self):
        """重置任务状态，允许开始新任务"""
        try:
            from videotrans.configure import config

            # 检查所有队列是否都为空
            all_queues_empty = (
                len(config.prepare_queue) == 0 and
                len(config.regcon_queue) == 0 and
                len(config.trans_queue) == 0 and
                len(config.dubb_queue) == 0 and
                len(config.align_queue) == 0 and
                len(config.assemb_queue) == 0
            )

            if all_queues_empty:
                config.current_status = 'stop'
                print("[DEBUG] Status reset to 'stop', ready for new tasks")
            else:
                print(f"[DEBUG] Cannot reset status, queues not empty: "
                      f"prepare={len(config.prepare_queue)}, "
                      f"regcon={len(config.regcon_queue)}, "
                      f"trans={len(config.trans_queue)}, "
                      f"dubb={len(config.dubb_queue)}, "
                      f"align={len(config.align_queue)}, "
                      f"assemb={len(config.assemb_queue)}")
        except Exception as e:
            print(f"Error in resetStatus: {e}")
            import traceback
            traceback.print_exc()

    @Slot(int, result=dict)
    def openTranslateSettings(self, translate_type: int) -> Dict[str, Any]:
        """打开翻译设置对话框"""
        try:
            from videotrans import translator, winform

            # 根据翻译类型打开对应的设置窗口
            if translate_type == translator.BAIDU_INDEX:
                winform.get_win('baidu').openwin()
            elif translate_type == translator.ALI_INDEX:
                winform.get_win('ali').openwin()
            elif translate_type == translator.TENCENT_INDEX:
                winform.get_win('tencent').openwin()
            elif translate_type == translator.CHATGPT_INDEX:
                winform.get_win('chatgpt').openwin()
            elif translate_type == translator.AZUREGPT_INDEX:
                winform.get_win('azure').openwin()
            elif translate_type == translator.GEMINI_INDEX:
                winform.get_win('gemini').openwin()
            elif translate_type == translator.CLAUDE_INDEX:
                winform.get_win('claude').openwin()
            elif translate_type == translator.DEEPL_INDEX:
                winform.get_win('deepL').openwin()
            elif translate_type == translator.DEEPLX_INDEX:
                winform.get_win('deepLX').openwin()
            elif translate_type == translator.LOCALLLM_INDEX:
                winform.get_win('localllm').openwin()
            elif translate_type == translator.ZIJIE_INDEX:
                winform.get_win('doubao').openwin()
            elif translate_type == translator.TRANSAPI_INDEX:
                winform.get_win('transapi').openwin()
            elif translate_type == translator.QWENMT_INDEX:
                winform.get_win('qwenmt').openwin()
            elif translate_type == translator.LIBRE_INDEX:
                winform.get_win('libre').openwin()
            elif translate_type == translator.AI302_INDEX:
                winform.get_win('ai302').openwin()
            elif translate_type == translator.ZHIPUAI_INDEX:
                winform.get_win('zhipuai').openwin()
            elif translate_type == translator.SILICONFLOW_INDEX:
                winform.get_win('siliconflow').openwin()
            elif translate_type == translator.DEEPSEEK_INDEX:
                winform.get_win('deepseek').openwin()
            elif translate_type == translator.OPENROUTER_INDEX:
                winform.get_win('openrouter').openwin()
            else:
                return {"success": False, "message": "当前翻译渠道无需配置"}

            return {"success": True}
        except Exception as e:
            return {"success": False, "message": str(e)}

    @Slot(int, result=dict)
    def openTtsSettings(self, tts_type: int) -> Dict[str, Any]:
        """打开配音设置对话框"""
        try:
            from videotrans import winform

            # 根据配音类型打开对应的设置窗口
            if tts_type == tts.AZURE_TTS:
                winform.get_win('azuretts').openwin()
            elif tts_type == tts.ELEVENLABS_TTS:
                winform.get_win('elevenlabs').openwin()
            elif tts_type == tts.AI302_TTS:
                winform.get_win('ai302tts').openwin()
            elif tts_type == tts.CLONE_VOICE_TTS:
                winform.get_win('clone').openwin()
            elif tts_type == tts.CHATTTS:
                winform.get_win('chattts').openwin()
            elif tts_type == tts.TTS_API:
                winform.get_win('ttsapi').openwin()
            elif tts_type == tts.GPTSOVITS_TTS:
                winform.get_win('gptsovits').openwin()
            elif tts_type == tts.COSYVOICE_TTS:
                winform.get_win('cosyvoice').openwin()
            elif tts_type == tts.F5_TTS:
                winform.get_win('f5tts').openwin()
            elif tts_type == tts.FISHTTS:
                winform.get_win('fishtts').openwin()
            elif tts_type == tts.OPENAI_TTS:
                winform.get_win('openaitts').openwin()
            elif tts_type == tts.VOLCENGINE_TTS:
                winform.get_win('volcenginetts').openwin()
            elif tts_type == tts.GOOGLECLOUD_TTS:
                winform.get_win('googlecloud').openwin()
            elif tts_type == tts.GEMINI_TTS:
                winform.get_win('geminitts').openwin()
            elif tts_type == tts.CHATTERBOX_TTS:
                winform.get_win('chatterbox').openwin()
            elif tts_type == tts.QWEN_TTS:
                winform.get_win('qwentts').openwin()
            elif tts_type == tts.KOKORO_TTS:
                winform.get_win('kokoro').openwin()
            else:
                return {"success": False, "message": "当前配音渠道无需配置"}

            return {"success": True}
        except Exception as e:
            return {"success": False, "message": str(e)}

    @Slot(int, result=dict)
    def openRecognSettings(self, recogn_type: int) -> Dict[str, Any]:
        """打开语音识别设置对话框"""
        try:
            from videotrans import winform

            # 根据识别类型打开对应的设置窗口
            if recogn_type == recognition.OPENAI_API:
                winform.get_win('openairecognapi').openwin()
            elif recogn_type == recognition.CUSTOM_API:
                winform.get_win('recognapi').openwin()
            elif recogn_type == recognition.DOUBAO_API:
                winform.get_win('doubao').openwin()
            elif recogn_type == recognition.Deepgram:
                winform.get_win('deepgram').openwin()
            elif recogn_type == recognition.AI_302:
                winform.get_win('ai302').openwin()
            elif recogn_type == recognition.ElevenLabs:
                winform.get_win('elevenlabs').openwin()
            elif recogn_type == recognition.GEMINI_SPEECH:
                winform.get_win('gemini').openwin()
            elif recogn_type == recognition.PARAKEET:
                winform.get_win('parakeet').openwin()
            elif recogn_type == recognition.QWEN3ASR:
                winform.get_win('qwenmt').openwin()
            elif recogn_type == recognition.STT_API:
                winform.get_win('stt').openwin()
            else:
                return {"success": False, "message": "当前识别渠道无需配置"}

            return {"success": True}
        except Exception as e:
            return {"success": False, "message": str(e)}

    @Slot(result=dict)
    def openHearSightConfig(self) -> Dict[str, Any]:
        """打开智能摘要配置对话框"""
        try:
            if self._main_window and hasattr(self._main_window, 'open_hearsight_config'):
                # 使用主窗口的方法打开配置对话框
                self._main_window.open_hearsight_config()
                return {"success": True}
            else:
                return {"success": False, "message": "无法打开配置对话框"}
        except Exception as e:
            import traceback
            error_msg = f"{str(e)}\n{traceback.format_exc()}"
            return {"success": False, "message": error_msg}

    @Slot(result=dict)
    def openSaveDir(self) -> Dict[str, Any]:
        """打开保存目录"""
        try:
            import platform
            import subprocess
            from pathlib import Path

            target_dir = config.params.get('target_dir', '')
            if not target_dir or target_dir == '.':
                return {
                    "success": False,
                    "message": "请先选择保存目录" if config.defaulelang == 'zh' else "Please select save directory first"
                }

            target_path = Path(target_dir)
            # 如果目录不存在，尝试创建
            if not target_path.exists():
                try:
                    target_path.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    return {
                        "success": False,
                        "message": f"{'无法创建目录' if config.defaulelang == 'zh' else 'Cannot create directory'}: {e}"
                    }

            # 使用跨平台方式打开文件夹
            system = platform.system()
            if system == 'Windows':
                os.startfile(target_path)
            elif system == 'Darwin':  # macOS
                subprocess.run(['open', target_path])
            else:  # Linux
                subprocess.run(['xdg-open', target_path])

            return {"success": True}
        except Exception as e:
            return {
                "success": False,
                "message": f"{'打开文件夹失败' if config.defaulelang == 'zh' else 'Failed to open folder'}: {e}"
            }

    @Slot(result=list)
    def getHearSightFolders(self) -> List[Dict[str, Any]]:
        """获取HearSight分类文件夹列表"""
        try:
            from videotrans.hearsight.vector_store import get_vector_store

            # 获取向量存储实例
            vector_store = get_vector_store()
            folders = vector_store.list_folders()

            # 转换为前端需要的格式
            result = [
                {
                    "value": None,
                    "label": "全部视频" if config.defaulelang == 'zh' else "All Videos",
                    "count": 0
                }
            ]

            for folder in folders:
                result.append({
                    "value": folder.get('folder_id', ''),
                    "label": folder.get('name', ''),
                    "count": folder.get('video_count', 0)
                })

            return result
        except Exception as e:
            print(f"Error getting HearSight folders: {e}")
            import traceback
            traceback.print_exc()
            # 出错时至少返回"全部视频"选项
            return [
                {
                    "value": None,
                    "label": "全部视频" if config.defaulelang == 'zh' else "All Videos",
                    "count": 0
                }
            ]

    @Slot(str)
    def setHearSightFolder(self, folder_id: str) -> None:
        """设置选中的HearSight分类文件夹"""
        try:
            # None 或空字符串表示"全部视频"
            config.params['hearsight_folder_id'] = folder_id if folder_id else None
            print(f"[HearSight] 选中分类文件夹: {folder_id or '全部视频'}")
        except Exception as e:
            print(f"Error setting HearSight folder: {e}")

