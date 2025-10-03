# -*- coding: utf-8 -*-
import logging
from dataclasses import dataclass
from typing import List, Union
from urllib.parse import quote

import requests
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_not_exception_type, before_log, after_log

from videotrans.configure import config
from videotrans.configure._except import NO_RETRY_EXCEPT
from videotrans.translator._base import BaseTrans

RETRY_NUMS = 3
RETRY_DELAY = 5


@dataclass
class MyMemory(BaseTrans):

    def __post_init__(self):
        super().__post_init__()
        self.aisendsrt = False
        pro = self._set_proxy(type='set')
        if pro:
            self.proxies = {"https": pro, "http": pro}

    @retry(retry=retry_if_not_exception_type(NO_RETRY_EXCEPT), stop=(stop_after_attempt(RETRY_NUMS)),
           wait=wait_fixed(RETRY_DELAY), before=before_log(config.logger, logging.INFO),
           after=after_log(config.logger, logging.INFO))
    def _item_task(self, data: Union[List[str], str]) -> str:
        """
        MyMemory 免费接口单次最多 500 个字符，这里做自动分片请求并合并结果。
        """
        if self._exit():
            return

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        }

        MAX_CHARS = 450  # 预留余量，避免触发 500 限制

        def translate_text(text: str) -> str:
            url = f"https://api.mymemory.translated.net/get?q={quote(text)}&langpair={self.source_code}|{self.target_code}"
            config.logger.info(f'[mymemory]请求数据:{url=}')
            response = requests.get(url, proxies=self.proxies, headers=headers, verify=False, timeout=300)
            config.logger.info(f'[mymemory]返回:{response.text=}')
            response.raise_for_status()
            re_result = response.json()
            return re_result["responseData"]["translatedText"].strip()

        # data 可能是 list[str] 或 str
        if isinstance(data, list):
            out_chunks: List[str] = []
            buf: List[str] = []
            buf_len = 0
            for line in data:
                line = line or ""
                add_len = len(line) + (1 if buf else 0)  # 加上换行
                if buf and buf_len + add_len > MAX_CHARS:
                    out_chunks.append(translate_text("\n".join(buf)))
                    buf = [line]
                    buf_len = len(line)
                else:
                    buf.append(line)
                    buf_len += add_len
            if buf:
                out_chunks.append(translate_text("\n".join(buf)))
            return "\n".join(out_chunks)
        else:
            text = data or ""
            if len(text) <= MAX_CHARS:
                return translate_text(text)
            parts: List[str] = []
            cur: List[str] = []
            cur_len = 0
            for seg in text.split("\n"):
                add = len(seg) + (1 if cur else 0)
                if cur and cur_len + add > MAX_CHARS:
                    parts.append("\n".join(cur))
                    cur = [seg]
                    cur_len = len(seg)
                else:
                    cur.append(seg)
                    cur_len += add
            if cur:
                parts.append("\n".join(cur))
            res = [translate_text(p) for p in parts]
            return "\n".join(res)
