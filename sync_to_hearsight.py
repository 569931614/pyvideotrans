"""
将已处理的视频数据同步到HearSight
"""
import json
import hashlib
import requests
from pathlib import Path

# 已处理的视频信息
videos = [
    {
        "title": "Nephrotic Syndrome ｜ Five  Minute Review!",
        "oss_url": "https://xhs-pro.oss-cn-hangzhou.aliyuncs.com/videos/2025-11-03/db015037_1、Nephrotic Syndrome ｜ Five  Minute Review!.mp4",
        "srt_file": "F:/智能体定制/20250904translateVideo/pyvideotrans/output/b12db5f4df/zh-cn.srt",
        "summary_file": "F:/智能体定制/20250904translateVideo/pyvideotrans/output/b12db5f4df/hearsight_summary.txt"
    },
    {
        "title": "Diffuse Proliferative Glomerulonephritis vs Membranoproliferative Glomerulonephritis ｜ DPGN vs MPGN",
        "oss_url": "https://xhs-pro.oss-cn-hangzhou.aliyuncs.com/videos/2025-11-03/601827a4_10、Diffuse Proliferative Glomerulonephritis vs Membranoproliferative Glomerulonephritis ｜ DPGN vs MPGN.mp4",
        "srt_file": "F:/智能体定制/20250904translateVideo/pyvideotrans/output/93ae30eb5a/zh-cn.srt",
        "summary_file": "F:/智能体定制/20250904translateVideo/pyvideotrans/output/93ae30eb5a/hearsight_summary.txt"
    }
]

def main():
    print("开始同步视频数据到HearSight...")

    # 导入必要的模块
    import sys
    sys.path.insert(0, str(Path(__file__).parent))

    from videotrans.hearsight.segment_merger import merge_srt_to_paragraphs
    from videotrans.hearsight.summarizer import generate_summary, generate_paragraph_summaries
    from videotrans.hearsight.vector_store import get_vector_store
    from videotrans.configure import config

    # 加载HearSight配置
    hearsight_cfg_file = Path(__file__).parent / 'hearsight_config.json'
    if hearsight_cfg_file.exists():
        with open(hearsight_cfg_file, 'r', encoding='utf-8') as f:
            config.hearsight_config = json.load(f)

    # HearSight本地存储路径
    hearsight_vector_path = Path(__file__).parent.parent / 'HearSight' / 'app_datas' / 'vector_db' / 'volcengine'
    hearsight_vector_path.mkdir(parents=True, exist_ok=True)

    vector_store = get_vector_store()

    for i, video in enumerate(videos, 1):
        print(f"\n[{i}/{len(videos)}] 处理: {video['title']}")

        srt_path = Path(video['srt_file'])
        if not srt_path.exists():
            print(f"  [WARNING] SRT文件不存在: {srt_path}")
            continue

        try:
            # 总是重新生成摘要以确保数据完整
            print(f"  → 重新生成摘要...")
            # 重新生成摘要
            merge_cfg = config.hearsight_config.get('merge', {})
            paragraphs = merge_srt_to_paragraphs(
                srt_path=str(srt_path),
                max_gap=merge_cfg.get('max_gap', 2.0),
                max_duration=merge_cfg.get('max_duration', 30.0),
                max_chars=merge_cfg.get('max_chars', 200)
            )

            llm_config = config.hearsight_config.get('llm', {})
            paragraphs_with_summaries = generate_paragraph_summaries(
                paragraphs=paragraphs,
                api_key=llm_config.get('api_key', ''),
                base_url=llm_config.get('base_url', 'https://api.openai.com/v1'),
                model=llm_config.get('model', 'gpt-3.5-turbo'),
                temperature=llm_config.get('temperature', 0.3),
                timeout=llm_config.get('timeout', 60)
            )

            summary = generate_summary(
                paragraphs=paragraphs_with_summaries,
                api_key=llm_config.get('api_key', ''),
                base_url=llm_config.get('base_url', 'https://api.openai.com/v1'),
                model=llm_config.get('model', 'gpt-3.5-turbo'),
                temperature=llm_config.get('temperature', 0.3),
                timeout=llm_config.get('timeout', 120)
            )

            # 保存摘要到文件
            summary_path = Path(video['summary_file'])
            summary_path.parent.mkdir(parents=True, exist_ok=True)
            with open(summary_path, 'w', encoding='utf-8') as f:
                f.write(f"整体摘要\n{'='*80}\n")
                f.write(f"主题: {summary.get('topic', '')}\n")
                f.write(f"总结: {summary.get('summary', '')}\n\n")
                f.write(f"段落摘要\n{'='*80}\n\n")
                for j, para in enumerate(paragraphs_with_summaries, 1):
                    f.write(f"段落 {j}\n")
                    f.write(f"时间: {para['start_time']} --> {para['end_time']}\n")
                    f.write(f"摘要: {para['summary']}\n")
                    f.write(f"原文:\n{para['text']}\n")
                    f.write("-" * 80 + "\n\n")

            # 生成transcript_id
            transcript_id = hashlib.md5(video['oss_url'].encode('utf-8')).hexdigest()[:16]

            # 准备metadata
            metadata = {
                'basename': video['title'],
                'title': video['title'],
                'transcript_id': transcript_id,
                'is_oss': True,
                'app_mode': 'translate'
            }

            # 存储到向量数据库
            print(f"  → 存储到向量数据库...")
            success = vector_store.store_summary(
                video_path=video['oss_url'],
                summary=summary,
                paragraphs=paragraphs_with_summaries,
                metadata=metadata,
                local_storage_path=str(hearsight_vector_path)
            )

            if success:
                print(f"  [OK] 向量库存储成功! transcript_id={transcript_id}")
            else:
                print(f"  [FAIL] 向量库存储失败")

            # 同步到 HearSight PostgreSQL (通过 API)
            print(f"  → 同步到 HearSight API...")
            try:
                # 读取SRT文件转换为segments
                segments = []
                with open(srt_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # 简单解析SRT (假设格式正确)
                    import re
                    pattern = r'(\d+)\n(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})\n([\s\S]*?)(?=\n\n\d+\n|\Z)'
                    matches = re.findall(pattern, content)
                    for match in matches:
                        idx, start_str, end_str, text = match
                        # 转换时间格式 HH:MM:SS,mmm -> 秒数
                        def time_to_seconds(time_str):
                            h, m, s = time_str.replace(',', '.').split(':')
                            return float(h) * 3600 + float(m) * 60 + float(s)

                        segments.append({
                            'start_time': time_to_seconds(start_str),
                            'end_time': time_to_seconds(end_str),
                            'text': text.strip()
                        })

                # 准备API payload
                api_payload = {
                    'media_path': video['oss_url'],
                    'segments': segments,
                    'paragraphs': paragraphs_with_summaries,
                    'summary': summary,
                    'metadata': metadata
                }

                # 调用HearSight API
                response = requests.post(
                    'http://localhost:9999/api/import/pyvideotrans',
                    json=api_payload,
                    timeout=60
                )

                if response.status_code == 200:
                    result = response.json()
                    print(f"  [OK] HearSight API同步成功! transcript_id={result.get('transcript_id')}")
                else:
                    print(f"  [FAIL] HearSight API同步失败: {response.status_code} - {response.text}")

            except Exception as api_error:
                print(f"  [ERROR] HearSight API调用失败: {api_error}")

        except Exception as e:
            print(f"  [ERROR] 错误: {e}")
            import traceback
            traceback.print_exc()

    print(f"\n完成！")

if __name__ == '__main__':
    main()
