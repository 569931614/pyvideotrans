"""
Qdrant向量存储适配器

适配pyvideotrans的Qdrant客户端，使其兼容HearSight摘要管理的接口
"""
import os
import json
import hashlib
import time
from datetime import datetime
from typing import List, Dict, Any, Optional
import uuid

from qdrant_client.models import Filter, FieldCondition, MatchValue

# 导入文件夹常量
from videotrans.hearsight.vector_store import (
    DEFAULT_FOLDER_ID,
    DEFAULT_FOLDER_NAME
)

# Qdrant需要UUID作为特殊点的ID
FOLDERS_REGISTRY_ID = str(uuid.UUID('00000000-0000-0000-0000-000000000001'))


class QdrantVectorStoreAdapter:
    """
    Qdrant向量存储适配器

    将pyvideotrans的QdrantVectorStore包装为兼容Volcengine/ChromaDB接口的类
    """

    def __init__(self, url: str = "http://localhost:6333", api_key: Optional[str] = None):
        """
        初始化Qdrant适配器

        Args:
            url: Qdrant服务器URL
            api_key: API密钥（可选）
        """
        # 延迟导入，避免循环依赖
        from videotrans.qdrant_export.qdrant_client import QdrantVectorStore

        self.client = QdrantVectorStore(url=url, api_key=api_key)
        self.qdrant_client = self.client.client  # 原始Qdrant客户端
        self.collection_chunks = self.client.collection_chunks
        self.collection_metadata = self.client.collection_metadata

        print(f"[QdrantAdapter] 已连接到 Qdrant: {url}")

        # 执行文件夹迁移
        self._migrate_folders()

    def _migrate_folders(self):
        """
        为现有视频添加默认文件夹元数据

        检查所有metadata中的视频，如果没有folder_id则添加默认文件夹
        """
        try:
            # 确保默认文件夹存在
            registry = self._get_folders_registry()
            folders = registry.get("folders", [])
            has_default = any(f["folder_id"] == DEFAULT_FOLDER_ID for f in folders)

            if not has_default:
                folders.insert(0, {
                    "folder_id": DEFAULT_FOLDER_ID,
                    "name": DEFAULT_FOLDER_NAME,
                    "created_at": datetime.now().isoformat(),
                    "video_count": 0
                })
                registry["folders"] = folders
                self._save_folders_registry(registry)
                print(f"[QdrantAdapter迁移] 创建默认文件夹: {DEFAULT_FOLDER_NAME}")

            # 获取所有metadata点
            result = self.qdrant_client.scroll(
                collection_name=self.collection_metadata,
                limit=1000,
                with_payload=True,
                with_vectors=True
            )

            if not result or not result[0]:
                return

            from qdrant_client.models import PointStruct
            points_to_update = []
            migrated_count = 0

            for point in result[0]:
                # 跳过folders_registry
                if point.id == FOLDERS_REGISTRY_ID:
                    continue

                payload = point.payload
                # 如果没有folder_id，添加默认文件夹
                if "folder_id" not in payload or not payload.get("folder_id"):
                    payload["folder_id"] = DEFAULT_FOLDER_ID
                    payload["folder"] = DEFAULT_FOLDER_NAME

                    points_to_update.append(PointStruct(
                        id=point.id,
                        vector=point.vector,
                        payload=payload
                    ))
                    migrated_count += 1

            # 批量更新
            if points_to_update:
                self.qdrant_client.upsert(
                    collection_name=self.collection_metadata,
                    points=points_to_update
                )
                print(f"[QdrantAdapter迁移] 成功迁移 {migrated_count} 个视频到默认文件夹")

        except Exception as e:
            print(f"[QdrantAdapter迁移] 文件夹迁移失败: {e}")
            import traceback
            traceback.print_exc()

    def list_all_videos(self, folder_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        列出所有已存储摘要的视频

        Args:
            folder_id: 可选，仅列出指定文件夹的视频

        Returns:
            List[Dict]: 视频列表，格式与Volcengine兼容
        """
        try:
            # 构建过滤条件
            scroll_filter = None
            if folder_id:
                scroll_filter = Filter(
                    must=[
                        FieldCondition(
                            key="folder_id",
                            match=MatchValue(value=folder_id)
                        )
                    ]
                )

            # 使用scroll API获取所有metadata
            result = self.qdrant_client.scroll(
                collection_name=self.collection_metadata,
                scroll_filter=scroll_filter,
                limit=1000,  # 假设不会超过1000个视频
                with_payload=True,
                with_vectors=False
            )

            videos = []
            if result and result[0]:  # result = (points, next_page_offset)
                for point in result[0]:
                    # 跳过folders_registry
                    if point.id == FOLDERS_REGISTRY_ID:
                        continue

                    payload = point.payload
                    videos.append({
                        "video_id": point.id,
                        "video_path": payload.get("video_path", ""),
                        "topic": payload.get("video_title", "无主题"),  # Qdrant存的是video_title
                        "paragraph_count": payload.get("chunk_count", 0),  # 使用chunk_count
                        "total_duration": payload.get("duration", 0.0),
                        "folder_id": payload.get("folder_id", DEFAULT_FOLDER_ID),
                        "folder": payload.get("folder", DEFAULT_FOLDER_NAME)
                    })

            print(f"[QdrantAdapter] 找到 {len(videos)} 个视频")
            return videos

        except Exception as e:
            print(f"[QdrantAdapter] 列出视频失败: {e}")
            import traceback
            traceback.print_exc()
            return []

    def get_video_summary(self, video_path: str) -> Optional[Dict[str, Any]]:
        """
        获取视频的完整摘要数据

        Args:
            video_path: 视频路径、OSS URL 或 video_id

        Returns:
            Optional[Dict]: 摘要数据（兼容Volcengine格式）
        """
        try:
            normalized_path = os.path.normpath(os.path.abspath(video_path))

            # 策略1: 尝试从所有 metadata 中查找匹配的 video_path（OSS URL 或本地路径）
            all_metadata = self.qdrant_client.scroll(
                collection_name=self.collection_metadata,
                limit=1000,
                with_payload=True,
                with_vectors=False
            )

            metadata_point = None
            if all_metadata and all_metadata[0]:
                for point in all_metadata[0]:
                    stored_path = point.payload.get("video_path", "")
                    # 尝试多种匹配：
                    # 1. 完全匹配（OSS URL）
                    # 2. 本地路径匹配
                    # 3. 文件名匹配
                    if (video_path == stored_path or
                        normalized_path == stored_path or
                        os.path.basename(video_path) in stored_path or
                        os.path.basename(normalized_path) in stored_path):
                        metadata_point = point
                        break

            if not metadata_point:
                print(f"[QdrantAdapter] 未找到视频元数据: {os.path.basename(video_path)}")
                return None

            metadata_payload = metadata_point.payload

            # 构建整体摘要
            video_title = metadata_payload.get("video_title", "无主题")
            video_summary = metadata_payload.get("video_summary", "")

            overall_doc = f"主题: {video_title}\n总结: {video_summary}" if video_summary else f"主题: {video_title}"

            overall_meta = {
                "video_id": str(metadata_point.id),
                "video_path": normalized_path,
                "type": "overall_summary",
                "topic": video_title,
                "paragraph_count": metadata_payload.get("chunk_count", 0),
                "total_duration": metadata_payload.get("duration", 0.0)
            }

            # 2. 从chunks collection获取所有段落（使用 video_id 查询）
            video_id = metadata_payload.get("video_id", "")
            chunks_result = self.qdrant_client.scroll(
                collection_name=self.collection_chunks,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(
                            key="video_id",
                            match=MatchValue(value=video_id)
                        )
                    ]
                ),
                limit=1000,  # 假设一个视频不会超过1000个chunks
                with_payload=True,
                with_vectors=False
            )

            paragraphs_list = []
            if chunks_result and chunks_result[0]:
                # 按chunk_index排序
                chunks = sorted(chunks_result[0], key=lambda p: p.payload.get("chunk_index", 0))

                for chunk_point in chunks:
                    chunk_payload = chunk_point.payload

                    chunk_text = chunk_payload.get("chunk_text", "")
                    para_summary = chunk_payload.get("paragraph_summary", "")

                    # 构建文档（与Volcengine格式兼容）
                    if para_summary:
                        para_doc = f"段落摘要: {para_summary}\n完整内容: {chunk_text}"
                    else:
                        para_doc = chunk_text

                    para_meta = {
                        "video_id": chunk_payload.get("video_id", ""),
                        "video_path": normalized_path,
                        "type": "paragraph",
                        "index": chunk_payload.get("chunk_index", 0),
                        "start_time": chunk_payload.get("start_time", 0.0),
                        "end_time": chunk_payload.get("end_time", 0.0),
                        "has_summary": bool(para_summary),
                        "paragraph_summary": para_summary
                    }

                    paragraphs_list.append({
                        "document": para_doc,
                        "metadata": para_meta
                    })

            result = {
                "video_path": normalized_path,
                "overall": {
                    "document": overall_doc,
                    "metadata": overall_meta
                },
                "paragraphs": paragraphs_list
            }

            print(f"[QdrantAdapter] 获取视频摘要成功: {video_title}, {len(paragraphs_list)} 段落")
            return result

        except Exception as e:
            print(f"[QdrantAdapter] 获取视频摘要失败: {e}")
            import traceback
            traceback.print_exc()
            return None

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
            video_id: 限制在特定视频中搜索（暂不支持）
            filter_type: 过滤类型（暂不支持）

        Returns:
            List[Dict]: 搜索结果列表
        """
        try:
            # 需要先生成查询向量
            from videotrans.configure import config
            from videotrans.qdrant_export.embedder import generate_embeddings

            # 获取embedding配置
            embedding_api_url = config.params.get('qdrant_embedding_api_url', '')
            embedding_api_key = config.params.get('qdrant_embedding_api_key', '')
            embedding_model = config.params.get('qdrant_embedding_model', 'BAAI/bge-large-zh-v1.5')

            if not embedding_api_url or not embedding_api_key:
                print("[QdrantAdapter] Embedding API未配置，无法进行搜索")
                return []

            # 生成查询向量
            query_vectors = generate_embeddings(
                texts=[query],
                embedding_api_url=embedding_api_url,
                embedding_api_key=embedding_api_key,
                embedding_model=embedding_model
            )

            if not query_vectors or len(query_vectors) == 0:
                print("[QdrantAdapter] 生成查询向量失败")
                return []

            query_vector = query_vectors[0]

            # 在chunks collection中搜索
            search_result = self.qdrant_client.search(
                collection_name=self.collection_chunks,
                query_vector=query_vector,
                limit=n_results
            )

            results = []
            for scored_point in search_result:
                payload = scored_point.payload

                # 计算距离（1 - score，因为Qdrant返回的是相似度分数）
                distance = 1.0 - scored_point.score

                results.append({
                    "document": payload.get("chunk_text", ""),
                    "metadata": {
                        "video_id": payload.get("video_id", ""),
                        "video_path": payload.get("video_path", ""),
                        "type": "paragraph",  # Qdrant中的chunks都是段落
                        "start_time": payload.get("start_time", 0.0),
                        "end_time": payload.get("end_time", 0.0),
                        "paragraph_summary": payload.get("paragraph_summary", "")
                    },
                    "id": str(scored_point.id),
                    "distance": distance,
                    "similarity": scored_point.score
                })

            print(f"[QdrantAdapter] 搜索返回 {len(results)} 个结果")
            return results

        except Exception as e:
            print(f"[QdrantAdapter] 搜索失败: {e}")
            import traceback
            traceback.print_exc()
            return []

    def delete_video(self, video_path: str) -> bool:
        """
        删除视频的所有摘要数据

        Args:
            video_path: 视频路径（可以是文件名、本地路径或OSS URL）

        Returns:
            bool: 是否删除成功
        """
        try:
            print(f"[QdrantAdapter] 准备删除视频: {video_path}")

            # 获取所有视频，进行智能匹配
            all_metadata = self.qdrant_client.scroll(
                collection_name=self.collection_metadata,
                limit=1000,
                with_payload=True,
                with_vectors=False
            )

            matched_paths = []
            if all_metadata and all_metadata[0]:
                for point in all_metadata[0]:
                    stored_path = point.payload.get("video_path", "")

                    # 策略1: 完全匹配
                    if video_path == stored_path:
                        matched_paths.append(stored_path)
                        print(f"[QdrantAdapter] 完全匹配: {stored_path}")
                        continue

                    # 策略2: 文件名匹配（支持OSS URL和本地路径）
                    video_filename = os.path.basename(video_path)
                    stored_filename = os.path.basename(stored_path)
                    if video_filename == stored_filename:
                        matched_paths.append(stored_path)
                        print(f"[QdrantAdapter] 文件名匹配: {stored_path}")
                        continue

                    # 策略3: URL路径匹配（处理OSS URL）
                    # 如果stored_path是URL，尝试从URL中提取文件名匹配
                    if stored_path.startswith(('http://', 'https://')):
                        # 从URL中提取文件名
                        url_filename = stored_path.split('/')[-1]
                        if video_filename == url_filename or video_path == url_filename:
                            matched_paths.append(stored_path)
                            print(f"[QdrantAdapter] URL文件名匹配: {stored_path}")
                            continue

                    # 策略4: 本地路径规范化匹配（只用于本地文件）
                    if not video_path.startswith(('http://', 'https://')) and \
                       not stored_path.startswith(('http://', 'https://')):
                        try:
                            normalized_input = os.path.normpath(os.path.abspath(video_path))
                            normalized_stored = os.path.normpath(os.path.abspath(stored_path))
                            if normalized_input == normalized_stored:
                                matched_paths.append(stored_path)
                                print(f"[QdrantAdapter] 规范化路径匹配: {stored_path}")
                                continue
                        except:
                            pass

            if not matched_paths:
                print(f"[QdrantAdapter] 未找到匹配的视频路径: {video_path}")
                return False

            # 删除所有匹配的路径
            success = False
            for matched_path in matched_paths:
                print(f"[QdrantAdapter] 尝试删除: {matched_path}")
                temp_success = self.client.delete_by_video_path(matched_path)
                if temp_success:
                    success = True
                    print(f"[QdrantAdapter] 删除成功: {matched_path}")
                else:
                    print(f"[QdrantAdapter] 删除失败: {matched_path}")

            if success:
                print(f"[QdrantAdapter] 删除视频成功: {os.path.basename(video_path)}")
            else:
                print(f"[QdrantAdapter] 删除视频失败: {os.path.basename(video_path)}")

            return success

        except Exception as e:
            print(f"[QdrantAdapter] 删除视频出错: {e}")
            import traceback
            traceback.print_exc()
            return False

    def store_summary(
        self,
        video_path: str,
        summary: Dict[str, Any],
        paragraphs: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None,
        local_storage_path: Optional[str] = None  # 兼容参数，Qdrant 不使用
    ) -> bool:
        """
        存储视频摘要到Qdrant

        注意：此方法不应直接调用，应通过pyvideotrans的导出流程

        Args:
            video_path: 视频文件路径
            summary: 整体摘要
            paragraphs: 段落列表
            metadata: 额外元数据
            local_storage_path: 本地存储路径（兼容参数，Qdrant不使用）

        Returns:
            bool: 是否存储成功
        """
        print("[QdrantAdapter] 警告: 不应直接调用store_summary，请使用pyvideotrans导出流程")
        return False

    def test_connection(self) -> bool:
        """
        测试Qdrant连接

        Returns:
            bool: 连接是否正常
        """
        try:
            collections = self.qdrant_client.get_collections()
            print(f"[QdrantAdapter] 连接成功，找到 {len(collections.collections)} 个集合")
            return True
        except Exception as e:
            print(f"[QdrantAdapter] 连接测试失败: {e}")
            return False

    # ==================== 文件夹管理方法 ====================

    def _generate_folder_id(self, folder_name: str) -> str:
        """生成文件夹唯一ID"""
        timestamp = str(time.time())
        raw = f"{folder_name}_{timestamp}"
        return hashlib.md5(raw.encode('utf-8')).hexdigest()[:12]

    def _get_folders_registry(self) -> Dict[str, Any]:
        """
        获取文件夹注册表（存储在metadata collection中）

        Qdrant使用特殊点ID存储文件夹注册表
        """
        try:
            # 从metadata collection获取folders_registry点
            result = self.qdrant_client.retrieve(
                collection_name=self.collection_metadata,
                ids=[FOLDERS_REGISTRY_ID]
            )

            if result and len(result) > 0:
                registry_json = result[0].payload.get('registry_data', '{}')
                return json.loads(registry_json)
        except Exception as e:
            print(f"[QdrantAdapter] 获取文件夹注册表失败: {e}")

        return {"folders": []}

    def _save_folders_registry(self, registry: Dict[str, Any]) -> bool:
        """保存文件夹注册表到Qdrant"""
        try:
            from qdrant_client.models import PointStruct

            # 删除旧的注册表点
            try:
                self.qdrant_client.delete(
                    collection_name=self.collection_metadata,
                    points_selector=[FOLDERS_REGISTRY_ID]
                )
            except:
                pass

            # 插入新的注册表点
            registry_json = json.dumps(registry, ensure_ascii=False)
            point = PointStruct(
                id=FOLDERS_REGISTRY_ID,
                vector=[0.0] * 1024,  # 占位向量（metadata collection需要）
                payload={
                    "type": "folder_registry",
                    "registry_data": registry_json
                }
            )

            self.qdrant_client.upsert(
                collection_name=self.collection_metadata,
                points=[point]
            )
            return True
        except Exception as e:
            print(f"[QdrantAdapter] 保存文件夹注册表失败: {e}")
            return False

    def create_folder(self, folder_name: str) -> Optional[str]:
        """创建新文件夹"""
        if not folder_name or not folder_name.strip():
            print("[QdrantAdapter] 文件夹名称不能为空")
            return None

        folder_name = folder_name.strip()
        registry = self._get_folders_registry()
        folders = registry.get("folders", [])

        # 检查名称是否已存在
        for folder in folders:
            if folder["name"] == folder_name:
                print(f"[QdrantAdapter] 文件夹名称已存在: {folder_name}")
                return None

        # 创建新文件夹
        folder_id = self._generate_folder_id(folder_name)
        new_folder = {
            "folder_id": folder_id,
            "name": folder_name,
            "created_at": datetime.now().isoformat(),
            "video_count": 0
        }
        folders.append(new_folder)

        registry["folders"] = folders
        if self._save_folders_registry(registry):
            print(f"[QdrantAdapter] 创建文件夹成功: {folder_name} (ID: {folder_id})")
            return folder_id
        else:
            return None

    def rename_folder(self, folder_id: str, new_name: str) -> bool:
        """重命名文件夹"""
        if not new_name or not new_name.strip():
            print("[QdrantAdapter] 文件夹名称不能为空")
            return False

        new_name = new_name.strip()

        if folder_id == DEFAULT_FOLDER_ID:
            print("[QdrantAdapter] 不能重命名默认文件夹")
            return False

        registry = self._get_folders_registry()
        folders = registry.get("folders", [])

        # 检查新名称是否已存在
        for folder in folders:
            if folder["name"] == new_name and folder["folder_id"] != folder_id:
                print(f"[QdrantAdapter] 文件夹名称已存在: {new_name}")
                return False

        # 查找并重命名
        found = False
        old_name = None
        for folder in folders:
            if folder["folder_id"] == folder_id:
                old_name = folder["name"]
                folder["name"] = new_name
                found = True
                break

        if not found:
            print(f"[QdrantAdapter] 未找到文件夹: {folder_id}")
            return False

        # 保存注册表
        registry["folders"] = folders
        if self._save_folders_registry(registry):
            # 更新所有视频的folder元数据
            try:
                # 获取该文件夹的所有视频（从metadata collection）
                result = self.qdrant_client.scroll(
                    collection_name=self.collection_metadata,
                    scroll_filter=Filter(
                        must=[
                            FieldCondition(
                                key="folder_id",
                                match=MatchValue(value=folder_id)
                            )
                        ]
                    ),
                    limit=1000
                )

                if result and result[0]:
                    from qdrant_client.models import PointStruct
                    points_to_update = []

                    for point in result[0]:
                        payload = point.payload.copy()
                        payload['folder'] = new_name

                        points_to_update.append(PointStruct(
                            id=point.id,
                            vector=point.vector,
                            payload=payload
                        ))

                    if points_to_update:
                        self.qdrant_client.upsert(
                            collection_name=self.collection_metadata,
                            points=points_to_update
                        )
            except Exception as e:
                print(f"[QdrantAdapter] 更新视频元数据失败: {e}")

            print(f"[QdrantAdapter] 重命名文件夹成功: {old_name} -> {new_name}")
            return True
        else:
            return False

    def delete_folder(self, folder_id: str, delete_videos: bool = False) -> bool:
        """删除文件夹"""
        if folder_id == DEFAULT_FOLDER_ID:
            print("[QdrantAdapter] 不能删除默认文件夹")
            return False

        registry = self._get_folders_registry()
        folders = registry.get("folders", [])

        # 查找文件夹
        folder_to_delete = None
        for i, folder in enumerate(folders):
            if folder["folder_id"] == folder_id:
                folder_to_delete = folder
                folders.pop(i)
                break

        if not folder_to_delete:
            print(f"[QdrantAdapter] 未找到文件夹: {folder_id}")
            return False

        try:
            # 获取该文件夹的所有视频
            result = self.qdrant_client.scroll(
                collection_name=self.collection_metadata,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(
                            key="folder_id",
                            match=MatchValue(value=folder_id)
                        )
                    ]
                ),
                limit=1000
            )

            if result and result[0]:
                video_ids = [point.id for point in result[0]]

                if delete_videos:
                    # 删除metadata
                    self.qdrant_client.delete(
                        collection_name=self.collection_metadata,
                        points_selector=video_ids
                    )

                    # 删除对应的chunks
                    for point in result[0]:
                        video_path = point.payload.get('video_path', '')
                        if video_path:
                            # 删除chunks
                            self.qdrant_client.delete(
                                collection_name=self.collection_chunks,
                                points_selector=Filter(
                                    must=[
                                        FieldCondition(
                                            key="video_path",
                                            match=MatchValue(value=video_path)
                                        )
                                    ]
                                )
                            )

                    print(f"[QdrantAdapter] 删除文件夹及 {len(video_ids)} 个视频")
                else:
                    # 移动到"未分类"文件夹
                    from qdrant_client.models import PointStruct
                    points_to_update = []

                    for point in result[0]:
                        payload = point.payload.copy()
                        payload['folder_id'] = DEFAULT_FOLDER_ID
                        payload['folder'] = DEFAULT_FOLDER_NAME

                        points_to_update.append(PointStruct(
                            id=point.id,
                            vector=point.vector,
                            payload=payload
                        ))

                    if points_to_update:
                        self.qdrant_client.upsert(
                            collection_name=self.collection_metadata,
                            points=points_to_update
                        )

                    print(f"[QdrantAdapter] 删除文件夹，{len(video_ids)} 个视频移动到'未分类'")

            # 保存注册表
            registry["folders"] = folders
            return self._save_folders_registry(registry)

        except Exception as e:
            print(f"[QdrantAdapter] 删除文件夹失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    def list_folders(self) -> List[Dict[str, Any]]:
        """列出所有文件夹"""
        registry = self._get_folders_registry()
        folders = registry.get("folders", [])

        # 确保默认文件夹存在
        has_default = any(f["folder_id"] == DEFAULT_FOLDER_ID for f in folders)
        if not has_default:
            folders.insert(0, {
                "folder_id": DEFAULT_FOLDER_ID,
                "name": DEFAULT_FOLDER_NAME,
                "created_at": datetime.now().isoformat(),
                "video_count": 0
            })

        # 更新每个文件夹的视频数量
        for folder in folders:
            try:
                result = self.qdrant_client.scroll(
                    collection_name=self.collection_metadata,
                    scroll_filter=Filter(
                        must=[
                            FieldCondition(
                                key="folder_id",
                                match=MatchValue(value=folder["folder_id"])
                            )
                        ]
                    ),
                    limit=1000,
                    with_payload=False,
                    with_vectors=False
                )
                folder["video_count"] = len(result[0]) if result and result[0] else 0
            except Exception as e:
                print(f"[QdrantAdapter] 获取文件夹视频数量失败: {e}")
                folder["video_count"] = 0

        return folders

    def assign_video_to_folder(self, video_path: str, folder_id: str) -> bool:
        """将视频分配到文件夹"""
        # 验证文件夹存在
        folders = self.list_folders()
        target_folder = None
        for folder in folders:
            if folder["folder_id"] == folder_id:
                target_folder = folder
                break

        if not target_folder:
            print(f"[QdrantAdapter] 文件夹不存在: {folder_id}")
            return False

        try:
            # 查找视频（智能匹配）
            normalized_path = os.path.normpath(os.path.abspath(video_path))

            result = self.qdrant_client.scroll(
                collection_name=self.collection_metadata,
                limit=1000,
                with_payload=True,
                with_vectors=True
            )

            if not result or not result[0]:
                print(f"[QdrantAdapter] 未找到视频: {video_path}")
                return False

            # 查找匹配的视频
            matched_point = None
            for point in result[0]:
                stored_path = point.payload.get("video_path", "")
                # 跳过folders_registry
                if point.id == FOLDERS_REGISTRY_ID:
                    continue

                if (stored_path == video_path or
                    stored_path == normalized_path or
                    os.path.basename(stored_path) == os.path.basename(video_path)):
                    matched_point = point
                    break

            if not matched_point:
                print(f"[QdrantAdapter] 未找到匹配的视频: {video_path}")
                return False

            # 更新metadata
            from qdrant_client.models import PointStruct
            payload = matched_point.payload.copy()
            payload['folder_id'] = folder_id
            payload['folder'] = target_folder["name"]

            self.qdrant_client.upsert(
                collection_name=self.collection_metadata,
                points=[PointStruct(
                    id=matched_point.id,
                    vector=matched_point.vector,
                    payload=payload
                )]
            )

            print(f"[QdrantAdapter] 视频移动到文件夹: {target_folder['name']}")
            return True

        except Exception as e:
            print(f"[QdrantAdapter] 分配视频到文件夹失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    def search_in_folder(
        self,
        query: str,
        folder_id: str,
        n_results: int = 5
    ) -> List[Dict[str, Any]]:
        """在指定文件夹中搜索"""
        try:
            # 先获取文件夹中的所有视频路径
            videos_result = self.qdrant_client.scroll(
                collection_name=self.collection_metadata,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(
                            key="folder_id",
                            match=MatchValue(value=folder_id)
                        )
                    ]
                ),
                limit=1000,
                with_payload=True,
                with_vectors=False
            )

            if not videos_result or not videos_result[0]:
                return []

            # 获取所有视频路径
            video_paths = [point.payload.get('video_path', '') for point in videos_result[0]]
            if not video_paths:
                return []

            # 生成查询向量
            from videotrans.configure import config
            from videotrans.qdrant_export.embedder import generate_embeddings

            embedding_api_url = config.params.get('qdrant_embedding_api_url', '')
            embedding_api_key = config.params.get('qdrant_embedding_api_key', '')
            embedding_model = config.params.get('qdrant_embedding_model', 'BAAI/bge-large-zh-v1.5')

            if not embedding_api_url or not embedding_api_key:
                print("[QdrantAdapter] Embedding API未配置")
                return []

            query_vectors = generate_embeddings(
                texts=[query],
                embedding_api_url=embedding_api_url,
                embedding_api_key=embedding_api_key,
                embedding_model=embedding_model
            )

            if not query_vectors:
                return []

            # 在chunks中搜索，但只返回这些视频的结果
            search_result = self.qdrant_client.search(
                collection_name=self.collection_chunks,
                query_vector=query_vectors[0],
                query_filter=Filter(
                    should=[
                        FieldCondition(
                            key="video_path",
                            match=MatchValue(value=vp)
                        ) for vp in video_paths
                    ]
                ),
                limit=n_results
            )

            results = []
            for scored_point in search_result:
                payload = scored_point.payload
                distance = 1.0 - scored_point.score

                results.append({
                    "document": payload.get("chunk_text", ""),
                    "metadata": {
                        "video_id": payload.get("video_id", ""),
                        "video_path": payload.get("video_path", ""),
                        "type": "paragraph",
                        "start_time": payload.get("start_time", 0.0),
                        "end_time": payload.get("end_time", 0.0),
                        "paragraph_summary": payload.get("paragraph_summary", ""),
                        "folder_id": folder_id
                    },
                    "id": str(scored_point.id),
                    "distance": distance,
                    "similarity": scored_point.score
                })

            print(f"[QdrantAdapter] 文件夹内搜索返回 {len(results)} 个结果")
            return results

        except Exception as e:
            print(f"[QdrantAdapter] 文件夹内搜索失败: {e}")
            import traceback
            traceback.print_exc()
            return []
