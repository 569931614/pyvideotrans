from __future__ import annotations

import os
from typing import List, Dict, Any

from PySide6.QtCore import QObject, Signal, Slot
from PySide6.QtWidgets import QFileDialog, QMessageBox

from videotrans.configure import config
from videotrans import recognition, tts
from videotrans.translator import TRANSLASTE_NAME_LIST


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

    # ========== Slots for JS ==========
    @Slot(result=dict)
    def getInitState(self) -> Dict[str, Any]:
        """Return initial state for Web UI to render controls."""
        try:
            state = {
                "version": getattr(self._main_window, "rawtitle", "pyvideotrans"),
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

    @Slot(result=list)
    def selectVideo(self) -> List[str]:
        """Open file dialog to select videos; return file paths list."""
        try:
            files, _ = QFileDialog.getOpenFileNames(
                self._main_window,
                "选择要处理的视频",
                config.params.get("target_dir", ""),
                "Video Files (*.mp4 *.mov *.mkv *.avi *.flv);;All Files (*)",
            )
            if files:
                # update default dir
                config.params["target_dir"] = os.path.dirname(files[0])
                # Set to queue_mp4 for processing
                self._set_video_queue(files)
            return files
        except Exception as e:
            QMessageBox.critical(self._main_window, "错误", f"选择视频失败：\n{e}")
            return []

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
                    "remove_noise"
                }:
                    config.params[key] = value
            self.notify.emit("paramsUpdated", {"params": params})
        except Exception as e:
            QMessageBox.critical(self._main_window, "错误", f"更新参数失败：\n{e}")

    @Slot(result=dict)
    def startTranslate(self) -> dict:
        """Start translation process using task queue system.

        Returns:
            dict: {'success': bool, 'task_uuids': [{'path': str, 'uuid': str}]}
        """
        try:
            from videotrans.util import tools
            from videotrans.task.trans_create import TransCreate
            from pathlib import Path

            win_action = self._ensure_main_action()

            # Check if already running
            if config.current_status == 'ing':
                QMessageBox.warning(self._main_window, "提示", "任务正在执行中...")
                return {'success': False, 'task_uuids': []}

            # Check if has videos
            if len(win_action.queue_mp4) < 1:
                QMessageBox.warning(self._main_window, "错误",
                    "必须选择视频文件" if config.defaulelang == 'zh' else "Video file must be selected")
                return {'success': False, 'task_uuids': []}

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
            }

            print(f"Starting translation with base config: {base_cfg}")
            print(f"Queue: {len(win_action.queue_mp4)} videos")

            # Store task UUID mapping for frontend
            task_uuids = []

            # Create and add tasks to queue for each video
            for video_path in win_action.queue_mp4:
                try:
                    # Create obj using format_video
                    obj = tools.format_video(video_path, config.params.get('target_dir', ''))
                    obj['target_dir'] = config.params.get('target_dir', '') + f'/{obj["uuid"]}'
                    obj['cache_folder'] = config.TEMP_DIR + f'/{obj["uuid"]}'

                    # Create directories
                    Path(obj['target_dir']).mkdir(parents=True, exist_ok=True)

                    # Merge obj into cfg
                    cfg = base_cfg.copy()
                    cfg.update(obj)

                    # Create task (only pass cfg)
                    task = TransCreate(cfg=cfg)

                    # Add to prepare queue
                    config.prepare_queue.append(task)
                    print(f"Task added to queue: {video_path}")

                    # Store UUID for frontend
                    task_uuids.append({
                        'path': video_path,
                        'uuid': obj['uuid']
                    })

                    # Set initial status
                    tools.set_process(
                        text=f"在队列中等待 No.{len(config.prepare_queue)}",
                        uuid=obj['uuid']
                    )

                except Exception as e:
                    print(f"Failed to create task for {video_path}: {e}")
                    import traceback
                    traceback.print_exc()

            # Update status
            config.current_status = 'ing'

            # Store task UUIDs for frontend retrieval
            config.params['_current_task_uuids'] = task_uuids

            QMessageBox.information(self._main_window, "提示",
                f"已添加 {len(win_action.queue_mp4)} 个任务到处理队列")

            return {'success': True, 'task_uuids': task_uuids}

        except Exception as e:
            print(f"Error in startTranslate: {e}")
            import traceback
            traceback.print_exc()
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

