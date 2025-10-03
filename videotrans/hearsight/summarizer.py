"""
LLM摘要生成模块

基于段落列表生成智能摘要
"""
from typing import List, Dict, Any, Optional
import json
from .chat_client import chat_with_openai


def build_summary_prompt(paragraphs: List[Dict[str, Any]]) -> str:
    """
    构建摘要生成的提示词

    Args:
        paragraphs: 段落列表

    Returns:
        str: 提示词
    """
    # 提示词模板
    header = """你是一个专业的内容总结助手。请基于以下带时间戳的段落内容，生成一个简洁准确的中文摘要。

要求：
1. 提炼内容的核心主题（topic）和关键信息
2. 生成一段简明的中文总结（summary），涵盖主要信息点
3. 避免流水账和冗余重复
4. 总结要准确反映原文内容，不要添加原文没有的信息
5. 输出格式必须是一个JSON对象，包含topic和summary两个字段

输出格式示例：
{"topic": "主题描述", "summary": "详细总结内容"}

下面是带时间戳的段落内容：
"""

    # 构建段落列表
    body_lines = []
    for para in paragraphs:
        start = para.get("start_time", 0.0)
        end = para.get("end_time", 0.0)
        text = para.get("text", "").strip()

        # 格式化时间
        start_str = f"{int(start//60):02d}:{int(start%60):02d}"
        end_str = f"{int(end//60):02d}:{int(end%60):02d}"

        body_lines.append(f"[{start_str} - {end_str}] {text}")

    footer = "\n请生成JSON格式的摘要（只输出JSON，不要包含任何其他文本）："

    return header + "\n\n" + "\n\n".join(body_lines) + "\n" + footer


def parse_summary_response(response: str) -> Dict[str, str]:
    """
    解析LLM返回的摘要结果

    Args:
        response: LLM返回的文本

    Returns:
        Dict: 包含topic和summary的字典
    """
    # 尝试直接解析JSON
    try:
        data = json.loads(response.strip())
        if isinstance(data, dict) and "topic" in data and "summary" in data:
            return {
                "topic": str(data["topic"]).strip(),
                "summary": str(data["summary"]).strip()
            }
    except json.JSONDecodeError:
        pass

    # 尝试从markdown代码块中提取JSON
    if "```" in response:
        try:
            # 查找代码块
            parts = response.split("```")
            for i in range(1, len(parts), 2):
                block = parts[i].strip()

                # 移除json标记
                if block.lower().startswith("json"):
                    block = block[4:].strip()

                # 尝试解析
                try:
                    data = json.loads(block)
                    if isinstance(data, dict) and "topic" in data and "summary" in data:
                        return {
                            "topic": str(data["topic"]).strip(),
                            "summary": str(data["summary"]).strip()
                        }
                except json.JSONDecodeError:
                    continue
        except Exception:
            pass

    # 如果都失败了，尝试使用简单规则提取
    lines = response.strip().split('\n')
    topic = ""
    summary = ""

    for line in lines:
        line = line.strip()
        if line.lower().startswith("topic:") or line.startswith("主题:"):
            topic = line.split(':', 1)[1].strip()
        elif line.lower().startswith("summary:") or line.startswith("总结:"):
            summary = line.split(':', 1)[1].strip()

    # 如果仍然没有提取到，把整个响应作为summary
    if not summary:
        summary = response.strip()

    return {
        "topic": topic,
        "summary": summary
    }


def generate_summary(
    paragraphs: List[Dict[str, Any]],
    api_key: str,
    base_url: str = "https://api.openai.com/v1",
    model: str = "gpt-3.5-turbo",
    temperature: float = 0.3,
    timeout: int = 120
) -> Dict[str, Any]:
    """
    生成视频内容摘要

    Args:
        paragraphs: 段落列表
        api_key: OpenAI API密钥
        base_url: API基础URL
        model: 模型名称
        temperature: 温度参数
        timeout: 超时时间（秒）

    Returns:
        Dict: 摘要结果，格式：
            {
                "topic": "主题",
                "summary": "摘要内容",
                "paragraph_count": 段落数量,
                "total_duration": 总时长（秒）
            }

    Raises:
        ValueError: 参数错误
        requests.HTTPError: API调用失败
    """
    if not paragraphs:
        raise ValueError("段落列表不能为空")

    if not api_key:
        raise ValueError("API密钥不能为空")

    # 构建提示词
    prompt = build_summary_prompt(paragraphs)

    # 调用LLM
    messages = [
        {
            "role": "user",
            "content": prompt
        }
    ]

    response = chat_with_openai(
        messages=messages,
        api_key=api_key,
        base_url=base_url,
        model=model,
        temperature=temperature,
        timeout=timeout
    )

    # 解析响应
    result = parse_summary_response(response)

    # 添加统计信息
    total_duration = 0.0
    if paragraphs:
        start = paragraphs[0].get("start_time", 0.0)
        end = paragraphs[-1].get("end_time", 0.0)
        total_duration = end - start

    result["paragraph_count"] = len(paragraphs)
    result["total_duration"] = total_duration

    return result


def generate_paragraph_summaries(
    paragraphs: List[Dict[str, Any]],
    api_key: str,
    base_url: str = "https://api.openai.com/v1",
    model: str = "gpt-3.5-turbo",
    temperature: float = 0.3,
    timeout: int = 60
) -> List[Dict[str, Any]]:
    """
    为每个段落生成单独的摘要

    Args:
        paragraphs: 段落列表
        api_key: OpenAI API密钥
        base_url: API基础URL
        model: 模型名称
        temperature: 温度参数
        timeout: 超时时间（秒）

    Returns:
        List[Dict]: 带摘要的段落列表，每个段落增加summary字段
    """
    if not paragraphs:
        return []

    if not api_key:
        raise ValueError("API密钥不能为空")

    results = []

    for i, para in enumerate(paragraphs):
        try:
            # 构建单个段落的提示词
            prompt = f"""请用一句话（不超过50字）总结以下内容的核心要点：

{para['text']}

只输出总结内容，不要有任何前缀或后缀。"""

            messages = [
                {
                    "role": "user",
                    "content": prompt
                }
            ]

            # 调用LLM
            summary_text = chat_with_openai(
                messages=messages,
                api_key=api_key,
                base_url=base_url,
                model=model,
                temperature=temperature,
                timeout=timeout
            )

            # 复制段落并添加摘要
            para_copy = para.copy()
            para_copy["summary"] = summary_text.strip()
            results.append(para_copy)

        except Exception as e:
            # 如果某个段落摘要生成失败，使用原文本作为摘要
            para_copy = para.copy()
            para_copy["summary"] = para["text"][:50] + "..."
            para_copy["summary_error"] = str(e)
            results.append(para_copy)

    return results


def export_summary_to_markdown(
    summary: Dict[str, Any],
    paragraphs: List[Dict[str, Any]],
    output_path: str
) -> None:
    """
    导出摘要为Markdown格式

    Args:
        summary: 整体摘要
        paragraphs: 段落列表
        output_path: 输出文件路径
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        # 写入标题和总摘要
        f.write(f"# {summary.get('topic', '视频内容摘要')}\n\n")
        f.write(f"## 总结\n\n")
        f.write(f"{summary.get('summary', '')}\n\n")

        # 写入统计信息
        para_count = summary.get('paragraph_count', len(paragraphs))
        duration = summary.get('total_duration', 0.0)
        duration_str = f"{int(duration//60)}:{int(duration%60):02d}"

        f.write(f"**段落数**: {para_count} | **总时长**: {duration_str}\n\n")
        f.write(f"---\n\n")

        # 写入段落详情
        f.write(f"## 详细内容\n\n")

        for para in paragraphs:
            start = para.get("start_time", 0.0)
            end = para.get("end_time", 0.0)
            text = para.get("text", "")

            start_str = f"{int(start//60):02d}:{int(start%60):02d}"
            end_str = f"{int(end//60):02d}:{int(end%60):02d}"

            f.write(f"### [{start_str} - {end_str}]\n\n")

            # 如果有段落级摘要，先显示摘要
            if "summary" in para and para["summary"] != text:
                f.write(f"**摘要**: {para['summary']}\n\n")

            f.write(f"{text}\n\n")
