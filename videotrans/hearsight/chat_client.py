"""
OpenAI兼容的聊天客户端

支持所有OpenAI API兼容的服务（ChatGPT、DeepSeek、Gemini等）
"""
from typing import List, Dict, Any, Optional
import requests
import json


def chat_with_openai(
    messages: List[Dict[str, str]],
    api_key: str,
    base_url: str = "https://api.openai.com/v1",
    model: str = "gpt-3.5-turbo",
    temperature: float = 0.3,
    timeout: int = 60,
    **kwargs
) -> str:
    """
    调用OpenAI兼容的Chat Completion API

    Args:
        messages: 消息列表，格式 [{"role": "user", "content": "..."}]
        api_key: API密钥
        base_url: API基础URL
        model: 模型名称
        temperature: 温度参数（0-1）
        timeout: 超时时间（秒）
        **kwargs: 其他API参数

    Returns:
        str: AI返回的文本内容

    Raises:
        requests.HTTPError: API调用失败
        ValueError: 参数错误
    """
    if not api_key:
        raise ValueError("api_key不能为空")

    if not messages:
        raise ValueError("messages不能为空")

    # 构造请求URL
    url = f"{base_url.rstrip('/')}/chat/completions"

    # 请求头
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    # 请求体
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
    }

    # 合并额外参数
    if kwargs:
        payload.update(kwargs)

    try:
        # 发送请求
        response = requests.post(
            url,
            json=payload,
            headers=headers,
            timeout=timeout
        )

        # 检查响应状态
        if not response.ok:
            raise requests.HTTPError(
                f"API调用失败: {response.status_code} {response.reason}\n"
                f"响应内容: {response.text}"
            )

        # 解析响应
        data = response.json()

        # 提取返回内容
        choices = data.get("choices", [])
        if not choices:
            raise ValueError("API返回的choices为空")

        message = choices[0].get("message", {})
        content = message.get("content", "")

        return content.strip()

    except requests.Timeout:
        raise TimeoutError(f"API调用超时（{timeout}秒）")
    except requests.RequestException as e:
        raise requests.HTTPError(f"网络请求失败: {str(e)}")
    except json.JSONDecodeError as e:
        raise ValueError(f"API返回的JSON格式错误: {str(e)}")


def chat_simple(
    prompt: str,
    api_key: str,
    base_url: str = "https://api.openai.com/v1",
    model: str = "gpt-3.5-turbo",
    system_message: Optional[str] = None,
    **kwargs
) -> str:
    """
    简化版聊天接口，直接传入prompt

    Args:
        prompt: 用户提示词
        api_key: API密钥
        base_url: API基础URL
        model: 模型名称
        system_message: 可选的系统消息
        **kwargs: 其他参数

    Returns:
        str: AI返回的文本
    """
    messages = []

    # 添加系统消息
    if system_message:
        messages.append({
            "role": "system",
            "content": system_message
        })

    # 添加用户消息
    messages.append({
        "role": "user",
        "content": prompt
    })

    return chat_with_openai(
        messages=messages,
        api_key=api_key,
        base_url=base_url,
        model=model,
        **kwargs
    )
