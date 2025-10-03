"""
智能段落合并模块

将Whisper生成的短句SRT合并为语义连贯的段落
"""
from typing import List, Dict, Any
import re


def parse_srt_file(srt_path: str) -> List[Dict[str, Any]]:
    """
    解析SRT字幕文件

    Args:
        srt_path: SRT文件路径

    Returns:
        List[Dict]: 字幕列表，格式：
            [
                {
                    "index": 1,
                    "start_time": 0.0,  # 秒
                    "end_time": 2.5,
                    "text": "字幕内容"
                },
                ...
            ]
    """
    segments = []

    with open(srt_path, 'r', encoding='utf-8') as f:
        content = f.read().strip()

    # 按空行分割字幕块
    blocks = content.split('\n\n')

    for block in blocks:
        lines = block.strip().split('\n')
        if len(lines) < 3:
            continue

        # 第一行：序号
        try:
            index = int(lines[0].strip())
        except:
            continue

        # 第二行：时间戳
        timestamp_line = lines[1].strip()
        match = re.match(
            r'(\d{2}):(\d{2}):(\d{2})[,.](\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2})[,.](\d{3})',
            timestamp_line
        )

        if not match:
            continue

        # 解析开始时间
        h1, m1, s1, ms1 = map(int, match.groups()[:4])
        start_time = h1 * 3600 + m1 * 60 + s1 + ms1 / 1000.0

        # 解析结束时间
        h2, m2, s2, ms2 = map(int, match.groups()[4:])
        end_time = h2 * 3600 + m2 * 60 + s2 + ms2 / 1000.0

        # 第三行及之后：字幕文本
        text = '\n'.join(lines[2:]).strip()

        segments.append({
            "index": index,
            "start_time": start_time,
            "end_time": end_time,
            "text": text
        })

    return segments


def merge_by_rules(
    segments: List[Dict[str, Any]],
    max_gap: float = 2.0,
    max_duration: float = 30.0,
    max_chars: int = 200
) -> List[Dict[str, Any]]:
    """
    基于规则的段落合并

    合并策略：
    1. 相邻字幕时间间隔小于max_gap秒时合并
    2. 合并后的段落时长不超过max_duration秒
    3. 合并后的段落字符数不超过max_chars
    4. 遇到句号、问号、感叹号等结束符号时倾向于分段

    Args:
        segments: 原始字幕段落列表
        max_gap: 最大时间间隔（秒）
        max_duration: 最大段落时长（秒）
        max_chars: 最大字符数

    Returns:
        List[Dict]: 合并后的段落列表
    """
    if not segments:
        return []

    paragraphs = []
    current = {
        "start_time": segments[0]["start_time"],
        "end_time": segments[0]["end_time"],
        "text": segments[0]["text"],
        "sentence_count": 1
    }

    # 句子结束符号
    end_punctuations = ['。', '！', '？', '.', '!', '?', '…']

    for i in range(1, len(segments)):
        seg = segments[i]
        prev = segments[i - 1]

        # 计算时间间隔
        gap = seg["start_time"] - prev["end_time"]

        # 计算合并后的时长和字符数
        merged_duration = seg["end_time"] - current["start_time"]
        merged_chars = len(current["text"]) + len(seg["text"])

        # 检查上一句是否以结束符号结尾
        ends_with_punctuation = any(
            current["text"].rstrip().endswith(p)
            for p in end_punctuations
        )

        # 决定是否合并
        should_merge = (
            gap <= max_gap and
            merged_duration <= max_duration and
            merged_chars <= max_chars and
            not (ends_with_punctuation and gap > 0.5)  # 句号后有明显停顿则分段
        )

        if should_merge:
            # 合并到当前段落
            current["end_time"] = seg["end_time"]
            current["text"] += " " + seg["text"]
            current["sentence_count"] += 1
        else:
            # 保存当前段落，开始新段落
            paragraphs.append(current)
            current = {
                "start_time": seg["start_time"],
                "end_time": seg["end_time"],
                "text": seg["text"],
                "sentence_count": 1
            }

    # 添加最后一个段落
    paragraphs.append(current)

    # 添加索引
    for idx, para in enumerate(paragraphs, start=1):
        para["index"] = idx

    return paragraphs


def merge_srt_to_paragraphs(
    srt_path: str,
    max_gap: float = 2.0,
    max_duration: float = 30.0,
    max_chars: int = 200
) -> List[Dict[str, Any]]:
    """
    将SRT字幕文件合并为段落

    Args:
        srt_path: SRT文件路径
        max_gap: 最大时间间隔（秒）
        max_duration: 最大段落时长（秒）
        max_chars: 最大字符数

    Returns:
        List[Dict]: 段落列表，格式：
            [
                {
                    "index": 1,
                    "start_time": 0.0,
                    "end_time": 15.5,
                    "text": "段落内容...",
                    "sentence_count": 5
                },
                ...
            ]
    """
    # 解析SRT文件
    segments = parse_srt_file(srt_path)

    if not segments:
        return []

    # 基于规则合并
    paragraphs = merge_by_rules(
        segments,
        max_gap=max_gap,
        max_duration=max_duration,
        max_chars=max_chars
    )

    return paragraphs


def format_time(seconds: float) -> str:
    """
    格式化时间为 HH:MM:SS 格式

    Args:
        seconds: 秒数

    Returns:
        str: 格式化的时间字符串
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)

    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes:02d}:{secs:02d}"


def export_paragraphs_to_text(
    paragraphs: List[Dict[str, Any]],
    output_path: str
) -> None:
    """
    导出段落为文本文件

    Args:
        paragraphs: 段落列表
        output_path: 输出文件路径
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        for para in paragraphs:
            start = format_time(para["start_time"])
            end = format_time(para["end_time"])
            f.write(f"[{start} - {end}]\n")
            f.write(f"{para['text']}\n\n")
