# -*- coding: utf-8 -*-
"""
PostgreSQL 数据库存储模块
用于将 pyvideotrans 处理的数据存储到与 HearSight 共享的 PostgreSQL 数据库
"""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def _ensure_psycopg2():
    """确保 psycopg2 已安装"""
    try:
        import psycopg2
        return True
    except ImportError:
        logger.warning("psycopg2 未安装，PostgreSQL 存储功能不可用。请运行: pip install psycopg2-binary")
        return False


def _get_db_params() -> Optional[Dict[str, Any]]:
    """
    从配置中获取数据库连接参数

    优先级:
    1. hearsight_config.json 中的配置
    2. 环境变量

    Returns:
        Dict[str, Any] or None: 数据库连接参数，如果未配置返回 None
    """
    from videotrans.configure import config

    # 尝试从 hearsight_config 读取
    hearsight_cfg = getattr(config, 'hearsight_config', None)
    if hearsight_cfg and isinstance(hearsight_cfg, dict):
        db_cfg = hearsight_cfg.get('database', {})
        if db_cfg:
            logger.info(f"使用 hearsight_config 中的数据库配置")
            return {
                "host": db_cfg.get('host', '127.0.0.1'),
                "port": int(db_cfg.get('port', 5432)),
                "user": db_cfg.get('user', 'postgres'),
                "password": db_cfg.get('password', ''),
                "dbname": db_cfg.get('database', 'hearsight')
            }

    # 尝试从环境变量读取
    if all(key in os.environ for key in ['POSTGRES_HOST', 'POSTGRES_USER', 'POSTGRES_DB']):
        logger.info(f"使用环境变量中的数据库配置")
        return {
            "host": os.environ.get('POSTGRES_HOST'),
            "port": int(os.environ.get('POSTGRES_PORT', 5432)),
            "user": os.environ.get('POSTGRES_USER'),
            "password": os.environ.get('POSTGRES_PASSWORD', ''),
            "dbname": os.environ.get('POSTGRES_DB')
        }

    logger.info("未找到数据库配置，PostgreSQL 存储功能不可用")
    return None


def is_enabled() -> bool:
    """检查 PostgreSQL 存储功能是否启用"""
    return _ensure_psycopg2() and _get_db_params() is not None


def save_transcript(media_path: str, segments: List[Dict[str, Any]]) -> Optional[int]:
    """
    保存转写记录到 PostgreSQL

    Args:
        media_path: 媒体文件路径
        segments: 分句列表 [{index, start_time, end_time, text}, ...]

    Returns:
        int or None: 新创建的 transcript_id，失败返回 None
    """
    if not _ensure_psycopg2():
        return None

    params = _get_db_params()
    if not params:
        return None

    try:
        import psycopg2

        conn = psycopg2.connect(**params)
        try:
            with conn:
                with conn.cursor() as cur:
                    # 转换为 JSON
                    segments_json = json.dumps(segments, ensure_ascii=False)

                    # 插入记录
                    cur.execute(
                        "INSERT INTO transcripts (media_path, segments_json) VALUES (%s, %s) RETURNING id",
                        (media_path, segments_json)
                    )
                    row = cur.fetchone()
                    if row:
                        transcript_id = int(row[0])
                        logger.info(f"✅ 转写记录已保存到 PostgreSQL: transcript_id={transcript_id}, 分句数={len(segments)}")
                        return transcript_id
                    return None
        finally:
            conn.close()

    except Exception as e:
        logger.error(f"保存转写记录到 PostgreSQL 失败: {e}")
        return None


def save_summaries(transcript_id: int, summaries: List[Dict[str, Any]]) -> Optional[int]:
    """
    保存摘要到 PostgreSQL

    Args:
        transcript_id: 关联的转写记录 ID
        summaries: 摘要列表

    Returns:
        int or None: 新创建的 summary_id，失败返回 None
    """
    if not _ensure_psycopg2():
        return None

    params = _get_db_params()
    if not params:
        return None

    try:
        import psycopg2

        conn = psycopg2.connect(**params)
        try:
            with conn:
                with conn.cursor() as cur:
                    summaries_json = json.dumps(summaries, ensure_ascii=False)

                    cur.execute(
                        "INSERT INTO summaries (transcript_id, summaries_json) VALUES (%s, %s) RETURNING id",
                        (transcript_id, summaries_json)
                    )
                    row = cur.fetchone()
                    if row:
                        summary_id = int(row[0])
                        logger.info(f"✅ 摘要已保存到 PostgreSQL: summary_id={summary_id}, 摘要数={len(summaries)}")
                        return summary_id
                    return None
        finally:
            conn.close()

    except Exception as e:
        logger.error(f"保存摘要到 PostgreSQL 失败: {e}")
        return None


def get_transcript_by_media_path(media_path: str) -> Optional[Dict[str, Any]]:
    """
    根据媒体路径获取最新的转写记录

    Args:
        media_path: 媒体文件路径

    Returns:
        Dict or None: 转写记录，包含 {id, media_path, segments, created_at}
    """
    if not _ensure_psycopg2():
        return None

    params = _get_db_params()
    if not params:
        return None

    try:
        import psycopg2
        from psycopg2.extras import RealDictCursor

        conn = psycopg2.connect(**params)
        try:
            with conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute(
                        """
                        SELECT id, media_path, segments_json, created_at
                        FROM transcripts
                        WHERE media_path = %s
                        ORDER BY id DESC
                        LIMIT 1
                        """,
                        (media_path,)
                    )
                    row = cur.fetchone()
                    if row:
                        segments = json.loads(row['segments_json'])
                        return {
                            'id': int(row['id']),
                            'media_path': str(row['media_path']),
                            'segments': segments,
                            'created_at': str(row['created_at'])
                        }
                    return None
        finally:
            conn.close()

    except Exception as e:
        logger.error(f"从 PostgreSQL 获取转写记录失败: {e}")
        return None


def list_all_videos() -> List[Dict[str, Any]]:
    """
    列出所有视频记录

    Returns:
        List[Dict]: 视频列表
    """
    if not _ensure_psycopg2():
        return []

    params = _get_db_params()
    if not params:
        return []

    try:
        import psycopg2
        from psycopg2.extras import RealDictCursor

        conn = psycopg2.connect(**params)
        try:
            with conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute(
                        """
                        SELECT id, media_path, created_at
                        FROM transcripts
                        ORDER BY id DESC
                        LIMIT 100
                        """
                    )
                    rows = cur.fetchall()
                    return [
                        {
                            'id': int(row['id']),
                            'media_path': str(row['media_path']),
                            'created_at': str(row['created_at'])
                        }
                        for row in rows
                    ]
        finally:
            conn.close()

    except Exception as e:
        logger.error(f"从 PostgreSQL 列出视频失败: {e}")
        return []
