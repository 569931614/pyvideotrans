"""
HearSight任务处理器

处理视频转写和摘要生成的完整流程
"""
from PySide6.QtCore import QThread, Signal
from typing import Optional, Dict, Any
import os


class HearSightProcessor(QThread):
    """HearSight处理线程"""

    # 信号
    progress_updated = Signal(str, int)  # 状态文本, 进度百分比
    finished = Signal(dict, list)  # 摘要, 段落列表
    error_occurred = Signal(str)  # 错误信息

    def __init__(
        self,
        srt_path: str,
        llm_config: Dict[str, Any],
        merge_config: Dict[str, Any],
        parent=None
    ):
        super().__init__(parent)

        self.srt_path = srt_path
        self.llm_config = llm_config
        self.merge_config = merge_config

    def run(self):
        """执行处理"""
        try:
            # 步骤1：检查文件
            self.progress_updated.emit("检查SRT文件...", 10)

            if not os.path.exists(self.srt_path):
                raise FileNotFoundError(f"SRT文件不存在: {self.srt_path}")

            # 步骤2：合并段落
            self.progress_updated.emit("正在合并段落...", 30)

            from videotrans.hearsight.segment_merger import merge_srt_to_paragraphs

            paragraphs = merge_srt_to_paragraphs(
                srt_path=self.srt_path,
                max_gap=self.merge_config.get('max_gap', 2.0),
                max_duration=self.merge_config.get('max_duration', 30.0),
                max_chars=self.merge_config.get('max_chars', 200)
            )

            if not paragraphs:
                raise ValueError("段落合并结果为空，请检查SRT文件格式")

            self.progress_updated.emit(f"段落合并完成，共{len(paragraphs)}个段落", 50)

            # 步骤3：生成整体摘要
            self.progress_updated.emit("正在生成整体摘要...", 60)

            from videotrans.hearsight.summarizer import generate_summary, generate_paragraph_summaries

            summary = generate_summary(
                paragraphs=paragraphs,
                api_key=self.llm_config['api_key'],
                base_url=self.llm_config['base_url'],
                model=self.llm_config['model'],
                temperature=self.llm_config.get('temperature', 0.3),
                timeout=self.llm_config.get('timeout', 120)
            )

            self.progress_updated.emit("整体摘要生成完成", 70)

            # 步骤4：为每个段落生成摘要
            self.progress_updated.emit(f"正在为每个段落生成摘要（共{len(paragraphs)}个）...", 75)

            paragraphs_with_summaries = generate_paragraph_summaries(
                paragraphs=paragraphs,
                api_key=self.llm_config['api_key'],
                base_url=self.llm_config['base_url'],
                model=self.llm_config['model'],
                temperature=self.llm_config.get('temperature', 0.3),
                timeout=self.llm_config.get('timeout', 60)
            )

            self.progress_updated.emit("段落摘要生成完成", 100)

            # 返回结果
            self.finished.emit(summary, paragraphs_with_summaries)

        except Exception as e:
            self.error_occurred.emit(str(e))
