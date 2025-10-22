"""
向量数据库存储模块

使用 ChromaDB 存储视频摘要和段落内容，支持语义检索
"""
import os
from typing import List, Dict, Any, Optional
import hashlib
import json


class VectorStore:
    """向量存储管理器"""

    def __init__(self, persist_directory: str = None):
        """
        初始化向量存储

        Args:
            persist_directory: 持久化目录路径
        """
        self.persist_directory = persist_directory
        self.collection = None
        self.client = None

    def _ensure_chromadb(self):
        """确保 ChromaDB 已安装"""
        try:
            import chromadb
            return True
        except ImportError:
            return False

    def initialize(self) -> bool:
        """
        初始化 ChromaDB 客户端

        Returns:
            bool: 初始化是否成功
        """
        if not self._ensure_chromadb():
            print("ChromaDB 未安装，请运行: pip install chromadb")
            return False

        try:
            import chromadb

            # 创建持久化客户端 (使用新版API)
            if self.persist_directory:
                os.makedirs(self.persist_directory, exist_ok=True)
                self.client = chromadb.PersistentClient(path=self.persist_directory)
            else:
                # 内存模式
                self.client = chromadb.EphemeralClient()

            # 获取或创建集合
            self.collection = self.client.get_or_create_collection(
                name="video_summaries",
                metadata={"hnsw:space": "cosine"}
            )

            return True

        except Exception as e:
            print(f"初始化 ChromaDB 失败: {e}")
            return False

    def _generate_video_id(self, video_path: str) -> str:
        """
        生成视频唯一ID

        Args:
            video_path: 视频路径

        Returns:
            str: 视频ID (MD5哈希)
        """
        return hashlib.md5(video_path.encode('utf-8')).hexdigest()

    def store_summary(
        self,
        video_path: str,
        summary: Dict[str, Any],
        paragraphs: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        存储视频摘要到向量库

        Args:
            video_path: 视频文件路径
            summary: 整体摘要 {topic, summary, ...}
            paragraphs: 段落列表 [{text, summary, start_time, end_time}, ...]
            metadata: 额外的元数据

        Returns:
            bool: 是否存储成功
        """
        if not self.collection:
            if not self.initialize():
                return False

        try:
            video_id = self._generate_video_id(video_path)

            # 准备文档、元数据和ID
            documents = []
            metadatas = []
            ids = []

            # 1. 存储整体摘要
            overall_doc = f"主题: {summary.get('topic', '')}\n总结: {summary.get('summary', '')}"
            documents.append(overall_doc)

            overall_meta = {
                "video_id": video_id,
                "video_path": video_path,
                "type": "overall_summary",
                "topic": summary.get('topic', ''),
                "paragraph_count": summary.get('paragraph_count', len(paragraphs)),
                "total_duration": float(summary.get('total_duration', 0.0))
            }

            if metadata:
                overall_meta.update(metadata)

            metadatas.append(overall_meta)
            ids.append(f"{video_id}_overall")

            # 2. 存储每个段落
            for i, para in enumerate(paragraphs):
                para_text = para.get('text', '')
                para_summary = para.get('summary', '')

                # 组合段落文本和摘要
                if para_summary:
                    para_doc = f"段落摘要: {para_summary}\n完整内容: {para_text}"
                else:
                    para_doc = para_text

                documents.append(para_doc)

                para_meta = {
                    "video_id": video_id,
                    "video_path": video_path,
                    "type": "paragraph",
                    "index": i,
                    "start_time": float(para.get('start_time', 0.0)),
                    "end_time": float(para.get('end_time', 0.0)),
                    "has_summary": bool(para_summary)
                }

                if para_summary:
                    para_meta["paragraph_summary"] = para_summary

                metadatas.append(para_meta)
                ids.append(f"{video_id}_para_{i}")

            # 批量添加到 ChromaDB
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )

            print(f"✅ 成功存储视频摘要: {os.path.basename(video_path)}")
            print(f"   - 整体摘要: 1 条")
            print(f"   - 段落摘要: {len(paragraphs)} 条")

            return True

        except Exception as e:
            print(f"❌ 存储摘要失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    def search(
        self,
        query: str,
        n_results: int = 5,
        video_id: Optional[str] = None,
        filter_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        语义搜索

        Args:
            query: 查询文本
            n_results: 返回结果数量
            video_id: 限制在特定视频中搜索
            filter_type: 过滤类型 ("overall_summary" 或 "paragraph")

        Returns:
            List[Dict]: 搜索结果列表
        """
        if not self.collection:
            if not self.initialize():
                return []

        try:
            # 构建过滤条件
            where = None
            conditions = []
            if video_id:
                conditions.append({"video_id": video_id})
            if filter_type:
                conditions.append({"type": filter_type})

            # 如果有多个条件，使用$and操作符
            if len(conditions) > 1:
                where = {"$and": conditions}
            elif len(conditions) == 1:
                where = conditions[0]

            # 执行查询
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where
            )

            # 格式化结果
            formatted_results = []
            if results and 'documents' in results:
                for i in range(len(results['documents'][0])):
                    formatted_results.append({
                        "document": results['documents'][0][i],
                        "metadata": results['metadatas'][0][i],
                        "id": results['ids'][0][i],
                        "distance": results['distances'][0][i] if 'distances' in results else None
                    })

            return formatted_results

        except Exception as e:
            print(f"❌ 搜索失败: {e}")
            return []

    def delete_video(self, video_path: str) -> bool:
        """
        删除视频的所有摘要数据

        Args:
            video_path: 视频路径

        Returns:
            bool: 是否删除成功
        """
        if not self.collection:
            if not self.initialize():
                return False

        try:
            video_id = self._generate_video_id(video_path)

            # 查找所有相关文档
            results = self.collection.get(
                where={"video_id": video_id}
            )

            if results and 'ids' in results:
                # 删除所有相关文档
                self.collection.delete(ids=results['ids'])
                print(f"✅ 已删除视频摘要: {os.path.basename(video_path)}")
                return True
            else:
                print(f"⚠️ 未找到视频摘要: {os.path.basename(video_path)}")
                return False

        except Exception as e:
            print(f"❌ 删除失败: {e}")
            return False

    def get_video_summary(self, video_path: str) -> Optional[Dict[str, Any]]:
        """
        获取视频的完整摘要数据

        Args:
            video_path: 视频路径

        Returns:
            Optional[Dict]: 摘要数据，如果不存在返回None
        """
        if not self.collection:
            if not self.initialize():
                return None

        try:
            video_id = self._generate_video_id(video_path)

            # 获取整体摘要
            overall = self.collection.get(
                ids=[f"{video_id}_overall"]
            )

            if not overall or not overall['documents']:
                return None

            # 获取所有段落
            paragraphs = self.collection.get(
                where={
                    "$and": [
                        {"video_id": video_id},
                        {"type": "paragraph"}
                    ]
                }
            )

            result = {
                "video_path": video_path,
                "overall": {
                    "document": overall['documents'][0],
                    "metadata": overall['metadatas'][0]
                },
                "paragraphs": []
            }

            if paragraphs and paragraphs['documents']:
                for i in range(len(paragraphs['documents'])):
                    result['paragraphs'].append({
                        "document": paragraphs['documents'][i],
                        "metadata": paragraphs['metadatas'][i]
                    })

            return result

        except Exception as e:
            print(f"❌ 获取摘要失败: {e}")
            return None

    def list_all_videos(self) -> List[Dict[str, Any]]:
        """
        列出所有已存储摘要的视频

        Returns:
            List[Dict]: 视频列表
        """
        if not self.collection:
            if not self.initialize():
                return []

        try:
            # 获取所有整体摘要
            results = self.collection.get(
                where={"type": "overall_summary"}
            )

            videos = []
            if results and 'metadatas' in results:
                for meta in results['metadatas']:
                    videos.append({
                        "video_id": meta.get("video_id"),
                        "video_path": meta.get("video_path"),
                        "topic": meta.get("topic"),
                        "paragraph_count": meta.get("paragraph_count"),
                        "total_duration": meta.get("total_duration")
                    })

            return videos

        except Exception as e:
            print(f"❌ 列出视频失败: {e}")
            return []


# 全局向量存储实例
_vector_store = None


def get_vector_store(persist_directory: str = None, force_backend: str = None):
    """
    获取全局向量存储实例，支持多种后端

    Args:
        persist_directory: 持久化目录路径
        force_backend: 强制使用的后端 ('chromadb' 或 'volcengine')

    Returns:
        VectorStore 或 VolcengineVectorClient: 向量存储实例
    """
    global _vector_store

    if _vector_store is None:
        from videotrans.configure import config

        # 确定使用哪个后端
        backend = force_backend
        if backend is None:
            # 从配置中读取
            hearsight_cfg = getattr(config, 'hearsight_config', {})
            vector_cfg = hearsight_cfg.get('vector', {})
            backend = vector_cfg.get('type', 'chromadb')

        # 根据backend创建实例
        if backend == 'volcengine':
            print("📊 使用火山引擎向量化服务")

            vector_cfg = getattr(config, 'hearsight_config', {}).get('vector', {})
            volc_cfg = vector_cfg.get('volcengine', {})

            from videotrans.hearsight.volcengine_vector import VolcengineVectorClient

            _vector_store = VolcengineVectorClient(
                api_key=volc_cfg.get('api_key', ''),
                base_url=volc_cfg.get('base_url', 'https://ark.cn-beijing.volces.com/api/v3'),
                collection_name=volc_cfg.get('collection_name', 'video_summaries'),
                embedding_model=volc_cfg.get('embedding_model', '')
            )
        else:
            print("📊 使用ChromaDB本地向量存储")

            # 优先使用传入的persist_directory，其次使用配置文件中的，最后使用默认路径
            if persist_directory is None:
                hearsight_cfg = getattr(config, 'hearsight_config', {})
                vector_cfg = hearsight_cfg.get('vector', {})
                persist_directory = vector_cfg.get('persist_directory')

                if persist_directory is None:
                    persist_directory = os.path.join(config.ROOT_DIR, 'vector_db')

                print(f"📁 向量库路径: {persist_directory}")

            _vector_store = VectorStore(persist_directory)
            _vector_store.initialize()

    return _vector_store


def reset_vector_store():
    """重置全局向量存储实例（用于切换后端）"""
    global _vector_store
    _vector_store = None
