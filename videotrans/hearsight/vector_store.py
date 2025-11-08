"""
向量数据库存储模块

使用 ChromaDB 存储视频摘要和段落内容，支持语义检索

## 文件夹数据模型

### Folder Metadata Schema
每个视频摘要包含文件夹元数据：
{
    "video_id": "abc123...",
    "video_path": "/path/to/video.mp4",
    "folder": "技术教程",           # 文件夹名称（默认："未分类"）
    "folder_id": "folder_123",      # 唯一文件夹标识符
    "type": "overall_summary",
    # ... 其他元数据
}

### Folders Registry
特殊文档存储文件夹定义：
{
    "id": "folders_registry",
    "type": "folder_registry",
    "folders": [
        {
            "folder_id": "folder_123",
            "name": "技术教程",
            "created_at": "2025-01-07T10:00:00",
            "video_count": 5
        },
        # ...
    ]
}

默认文件夹ID常量：
- DEFAULT_FOLDER_ID = "uncategorized"
- DEFAULT_FOLDER_NAME = "未分类"
"""
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import hashlib
import json
import time
from datetime import datetime

# 默认文件夹常量
DEFAULT_FOLDER_ID = "uncategorized"
DEFAULT_FOLDER_NAME = "未分类"
FOLDERS_REGISTRY_ID = "folders_registry"


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

            # 执行文件夹迁移（首次运行时）
            self._migrate_folders()

            return True

        except Exception as e:
            print(f"初始化 ChromaDB 失败: {e}")
            return False

    def _migrate_folders(self):
        """
        迁移现有视频到文件夹系统

        为所有没有folder_id的视频添加默认文件夹
        """
        if not self.collection:
            return

        try:
            # 检查是否需要迁移
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
                registry["folders"] = folders
                self._save_folders_registry(registry)
                print(f"[迁移] 创建默认文件夹: {DEFAULT_FOLDER_NAME}")

            # 查找所有没有folder_id的文档
            results = self.collection.get()

            if not results or not results['ids']:
                return

            migrated_count = 0
            for i, doc_id in enumerate(results['ids']):
                metadata = results['metadatas'][i]

                # 跳过文件夹注册表文档
                if metadata.get("type") == "folder_registry":
                    continue

                # 如果没有folder_id，添加默认文件夹
                if "folder_id" not in metadata or not metadata.get("folder_id"):
                    metadata["folder_id"] = DEFAULT_FOLDER_ID
                    metadata["folder"] = DEFAULT_FOLDER_NAME

                    try:
                        self.collection.update(
                            ids=[doc_id],
                            metadatas=[metadata]
                        )
                        migrated_count += 1
                    except Exception as e:
                        print(f"[迁移] 更新文档失败 {doc_id}: {e}")

            if migrated_count > 0:
                print(f"[迁移] 成功迁移 {migrated_count} 个文档到默认文件夹")

        except Exception as e:
            print(f"[迁移] 文件夹迁移失败: {e}")

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
        metadata: Optional[Dict[str, Any]] = None,
        folder_id: Optional[str] = None
    ) -> bool:
        """
        存储视频摘要到向量库

        Args:
            video_path: 视频文件路径
            summary: 整体摘要 {topic, summary, ...}
            paragraphs: 段落列表 [{text, summary, start_time, end_time}, ...]
            metadata: 额外的元数据
            folder_id: 文件夹ID（可选，默认使用"未分类"）

        Returns:
            bool: 是否存储成功
        """
        if not self.collection:
            if not self.initialize():
                return False

        try:
            video_id = self._generate_video_id(video_path)

            # 确定文件夹信息
            if folder_id is None:
                folder_id = DEFAULT_FOLDER_ID
                folder_name = DEFAULT_FOLDER_NAME
            else:
                # 验证文件夹存在并获取名称
                folders = self.list_folders()
                folder_name = DEFAULT_FOLDER_NAME
                for folder in folders:
                    if folder["folder_id"] == folder_id:
                        folder_name = folder["name"]
                        break

            documents: List[str] = []
            metadatas: List[Dict[str, Any]] = []
            ids: List[str] = []

            # 清理旧数据以避免重复ID
            try:
                self.collection.delete(where={"video_id": video_id})
            except Exception as delete_err:
                print(f"[vector] 删除旧向量数据失败: {delete_err}")

            # 1. 存储整体摘要
            overall_doc = f"主题: {summary.get('topic', '')}\n总结: {summary.get('summary', '')}"
            documents.append(overall_doc)

            overall_meta = {
                "video_id": video_id,
                "video_path": video_path,
                "type": "overall_summary",
                "topic": summary.get('topic', ''),
                "paragraph_count": summary.get('paragraph_count', len(paragraphs)),
                "total_duration": float(summary.get('total_duration', 0.0)),
                "folder_id": folder_id,
                "folder": folder_name
            }

            if metadata:
                overall_meta.update(metadata)

            metadatas.append(overall_meta)
            ids.append(f"{video_id}_overall")

            # 2. 存储每个段落
            for i, para in enumerate(paragraphs):
                para_text = para.get('text', '')
                para_summary = para.get('summary', '')

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
                    "has_summary": bool(para_summary),
                    "folder_id": folder_id,
                    "folder": folder_name
                }

                if para_summary:
                    para_meta["paragraph_summary"] = para_summary

                if metadata:
                    para_meta.update(metadata)

                metadatas.append(para_meta)
                ids.append(f"{video_id}_para_{i}")

            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )

            print(f"[vector] 成功存储视频摘要: {os.path.basename(video_path)}")
            print(f"         段落数量: {len(paragraphs)}")
            print(f"         文件夹: {folder_name}")

            return True

        except Exception as e:
            print(f"[vector] 存储摘要失败: {e}")
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
            print(f"[vector] 搜索失败: {e}")
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
                print(f"[vector] 已删除视频摘要: {os.path.basename(video_path)}")
                return True
            else:
                print(f"[vector] 未找到视频摘要: {os.path.basename(video_path)}")
                return False

        except Exception as e:
            print(f"[vector] 删除失败: {e}")
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
            print(f"[vector] 获取摘要失败: {e}")
            return None

    def list_all_videos(self, folder_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        列出所有已存储摘要的视频

        Args:
            folder_id: 可选，仅列出指定文件夹的视频

        Returns:
            List[Dict]: 视频列表
        """
        if not self.collection:
            if not self.initialize():
                return []

        try:
            # 构建查询条件
            if folder_id:
                where = {
                    "$and": [
                        {"type": "overall_summary"},
                        {"folder_id": folder_id}
                    ]
                }
            else:
                where = {"type": "overall_summary"}

            # 获取所有整体摘要
            results = self.collection.get(where=where)

            videos = []
            if results and 'metadatas' in results:
                for meta in results['metadatas']:
                    videos.append({
                        "video_id": meta.get("video_id"),
                        "video_path": meta.get("video_path"),
                        "topic": meta.get("topic"),
                        "paragraph_count": meta.get("paragraph_count"),
                        "total_duration": meta.get("total_duration"),
                        "folder_id": meta.get("folder_id", DEFAULT_FOLDER_ID),
                        "folder": meta.get("folder", DEFAULT_FOLDER_NAME)
                    })

            return videos

        except Exception as e:
            print(f"[vector] 列出视频失败: {e}")
            return []

    # ==================== 文件夹管理方法 ====================

    def _generate_folder_id(self, folder_name: str) -> str:
        """
        生成文件夹唯一ID

        Args:
            folder_name: 文件夹名称

        Returns:
            str: 文件夹ID
        """
        # 使用时间戳和名称生成唯一ID
        timestamp = str(time.time())
        raw = f"{folder_name}_{timestamp}"
        return hashlib.md5(raw.encode('utf-8')).hexdigest()[:12]

    def _get_folders_registry(self) -> Dict[str, Any]:
        """
        获取文件夹注册表

        Returns:
            Dict: 文件夹注册表数据
        """
        if not self.collection:
            if not self.initialize():
                return {"folders": []}

        try:
            result = self.collection.get(ids=[FOLDERS_REGISTRY_ID])
            if result and result['documents']:
                # 从文档中解析JSON
                registry_data = json.loads(result['documents'][0])
                return registry_data
        except Exception as e:
            print(f"[vector] 获取文件夹注册表失败: {e}")

        # 返回默认结构
        return {"folders": []}

    def _save_folders_registry(self, registry: Dict[str, Any]) -> bool:
        """
        保存文件夹注册表

        Args:
            registry: 文件夹注册表数据

        Returns:
            bool: 是否保存成功
        """
        if not self.collection:
            if not self.initialize():
                return False

        try:
            # 删除旧的注册表
            try:
                self.collection.delete(ids=[FOLDERS_REGISTRY_ID])
            except:
                pass

            # 保存新的注册表
            registry_json = json.dumps(registry, ensure_ascii=False)
            self.collection.add(
                documents=[registry_json],
                metadatas=[{"type": "folder_registry"}],
                ids=[FOLDERS_REGISTRY_ID]
            )
            return True
        except Exception as e:
            print(f"[vector] 保存文件夹注册表失败: {e}")
            return False

    def create_folder(self, folder_name: str) -> Optional[str]:
        """
        创建新文件夹

        Args:
            folder_name: 文件夹名称

        Returns:
            Optional[str]: 文件夹ID，如果失败则返回None
        """
        if not folder_name or not folder_name.strip():
            print("[vector] 文件夹名称不能为空")
            return None

        folder_name = folder_name.strip()

        # 获取现有文件夹
        registry = self._get_folders_registry()
        folders = registry.get("folders", [])

        # 检查名称是否已存在
        for folder in folders:
            if folder["name"] == folder_name:
                print(f"[vector] 文件夹名称已存在: {folder_name}")
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

        # 保存注册表
        registry["folders"] = folders
        if self._save_folders_registry(registry):
            print(f"[vector] 创建文件夹成功: {folder_name} (ID: {folder_id})")
            return folder_id
        else:
            return None

    def rename_folder(self, folder_id: str, new_name: str) -> bool:
        """
        重命名文件夹

        Args:
            folder_id: 文件夹ID
            new_name: 新名称

        Returns:
            bool: 是否成功
        """
        if not new_name or not new_name.strip():
            print("[vector] 文件夹名称不能为空")
            return False

        new_name = new_name.strip()

        # 不允许重命名默认文件夹
        if folder_id == DEFAULT_FOLDER_ID:
            print("[vector] 不能重命名默认文件夹")
            return False

        registry = self._get_folders_registry()
        folders = registry.get("folders", [])

        # 检查新名称是否已存在
        for folder in folders:
            if folder["name"] == new_name and folder["folder_id"] != folder_id:
                print(f"[vector] 文件夹名称已存在: {new_name}")
                return False

        # 查找并重命名
        found = False
        for folder in folders:
            if folder["folder_id"] == folder_id:
                old_name = folder["name"]
                folder["name"] = new_name
                found = True
                break

        if not found:
            print(f"[vector] 未找到文件夹: {folder_id}")
            return False

        # 保存注册表
        registry["folders"] = folders
        if self._save_folders_registry(registry):
            # 更新所有视频的folder元数据
            try:
                # 获取该文件夹的所有视频
                results = self.collection.get(
                    where={"folder_id": folder_id}
                )
                if results and results['ids']:
                    # 更新每个视频的metadata
                    for i, doc_id in enumerate(results['ids']):
                        metadata = results['metadatas'][i]
                        metadata['folder'] = new_name
                        # ChromaDB需要删除后重新添加来更新metadata
                        self.collection.update(
                            ids=[doc_id],
                            metadatas=[metadata]
                        )
            except Exception as e:
                print(f"[vector] 更新视频元数据失败: {e}")

            print(f"[vector] 重命名文件夹成功: {old_name} -> {new_name}")
            return True
        else:
            return False

    def delete_folder(self, folder_id: str, delete_videos: bool = False) -> bool:
        """
        删除文件夹

        Args:
            folder_id: 文件夹ID
            delete_videos: 是否同时删除文件夹中的视频（False则移动到"未分类"）

        Returns:
            bool: 是否成功
        """
        # 不允许删除默认文件夹
        if folder_id == DEFAULT_FOLDER_ID:
            print("[vector] 不能删除默认文件夹")
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
            print(f"[vector] 未找到文件夹: {folder_id}")
            return False

        try:
            # 获取该文件夹的所有视频
            results = self.collection.get(
                where={"folder_id": folder_id}
            )

            if results and results['ids']:
                if delete_videos:
                    # 删除所有视频
                    self.collection.delete(ids=results['ids'])
                    print(f"[vector] 删除文件夹及 {len(results['ids'])} 个视频")
                else:
                    # 移动到"未分类"文件夹
                    for i, doc_id in enumerate(results['ids']):
                        metadata = results['metadatas'][i]
                        metadata['folder_id'] = DEFAULT_FOLDER_ID
                        metadata['folder'] = DEFAULT_FOLDER_NAME
                        self.collection.update(
                            ids=[doc_id],
                            metadatas=[metadata]
                        )
                    print(f"[vector] 删除文件夹，{len(results['ids'])} 个视频移动到'未分类'")

            # 保存注册表
            registry["folders"] = folders
            return self._save_folders_registry(registry)

        except Exception as e:
            print(f"[vector] 删除文件夹失败: {e}")
            return False

    def list_folders(self) -> List[Dict[str, Any]]:
        """
        列出所有文件夹

        Returns:
            List[Dict]: 文件夹列表，包含video_count
        """
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
        if self.collection:
            for folder in folders:
                try:
                    results = self.collection.get(
                        where={
                            "$and": [
                                {"folder_id": folder["folder_id"]},
                                {"type": "overall_summary"}
                            ]
                        }
                    )
                    folder["video_count"] = len(results['ids']) if results and results['ids'] else 0
                except Exception as e:
                    print(f"[vector] 获取文件夹视频数量失败: {e}")
                    folder["video_count"] = 0

        return folders

    def assign_video_to_folder(self, video_path: str, folder_id: str) -> bool:
        """
        将视频分配到文件夹

        Args:
            video_path: 视频路径
            folder_id: 目标文件夹ID

        Returns:
            bool: 是否成功
        """
        if not self.collection:
            if not self.initialize():
                return False

        # 验证文件夹存在
        folders = self.list_folders()
        target_folder = None
        for folder in folders:
            if folder["folder_id"] == folder_id:
                target_folder = folder
                break

        if not target_folder:
            print(f"[vector] 文件夹不存在: {folder_id}")
            return False

        try:
            video_id = self._generate_video_id(video_path)

            # 获取该视频的所有文档
            results = self.collection.get(
                where={"video_id": video_id}
            )

            if not results or not results['ids']:
                print(f"[vector] 未找到视频: {video_path}")
                return False

            # 更新所有文档的folder元数据
            for i, doc_id in enumerate(results['ids']):
                metadata = results['metadatas'][i]
                metadata['folder_id'] = folder_id
                metadata['folder'] = target_folder["name"]
                self.collection.update(
                    ids=[doc_id],
                    metadatas=[metadata]
                )

            print(f"[vector] 视频移动到文件夹: {target_folder['name']}")
            return True

        except Exception as e:
            print(f"[vector] 分配视频到文件夹失败: {e}")
            return False

    def search_in_folder(
        self,
        query: str,
        folder_id: str,
        n_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        在指定文件夹中搜索

        Args:
            query: 查询文本
            folder_id: 文件夹ID
            n_results: 返回结果数量

        Returns:
            List[Dict]: 搜索结果列表
        """
        if not self.collection:
            if not self.initialize():
                return []

        try:
            # 执行查询，限制在指定文件夹
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
                where={"folder_id": folder_id}
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
            print(f"[vector] 文件夹内搜索失败: {e}")
            return []


# 全局向量存储实例
_vector_store = None


def get_vector_store(persist_directory: str = None, force_backend: str = None):
    """
    获取全局向量存储实例，支持多种后端

    Args:
        persist_directory: 持久化目录路径
        force_backend: 强制使用的后端('chromadb', 'volcengine', 'postgresql', 'qdrant')

    Returns:
        VectorStore, VolcengineVectorClient, PostgreSQLVectorStore 或 QdrantVectorStoreAdapter: 向量存储实例
    """
    global _vector_store

    from videotrans.configure import config

    backend = force_backend
    if backend is None:
        hearsight_cfg = getattr(config, 'hearsight_config', {})
        vector_cfg = hearsight_cfg.get('vector', {})
        backend = vector_cfg.get('type', 'chromadb')

    # 优先检查是否启用Qdrant作为主存储
    # 如果 qdrant_enabled=true 且 qdrant_as_primary=true，使用Qdrant
    if backend is None or backend == 'chromadb':  # 默认后端
        qdrant_enabled = config.params.get('qdrant_enabled', False)
        qdrant_as_primary = config.params.get('qdrant_as_primary', False)

        if qdrant_enabled and qdrant_as_primary:
            backend = 'qdrant'
            print('[vector] 检测到 qdrant_as_primary=true，切换到 Qdrant 后端')

    # Qdrant后端（新增）
    if backend == 'qdrant':
        from videotrans.hearsight.qdrant_vector_adapter import QdrantVectorStoreAdapter

        qdrant_url = config.params.get('qdrant_url', 'http://localhost:6333')
        qdrant_api_key = config.params.get('qdrant_api_key', None)

        if not isinstance(_vector_store, QdrantVectorStoreAdapter):
            print('[vector] Using Qdrant vector backend')
            print(f'[vector] Qdrant URL: {qdrant_url}')
            _vector_store = QdrantVectorStoreAdapter(url=qdrant_url, api_key=qdrant_api_key)

            # 测试连接
            if not _vector_store.test_connection():
                print('[vector] ⚠️ Qdrant连接失败，将降级到Volcengine后端')
                backend = 'volcengine'  # 降级
                _vector_store = None
            else:
                return _vector_store
        else:
            return _vector_store

    if backend == 'postgresql':
        from videotrans.hearsight.postgresql_vector_store import PostgreSQLVectorStore

        # 获取数据库配置（正确路径：vector.database）
        hearsight_cfg = getattr(config, 'hearsight_config', {})
        db_config = hearsight_cfg.get('vector', {}).get('database', {})

        if not isinstance(_vector_store, PostgreSQLVectorStore):
            print('[vector] Using PostgreSQL vector backend')
            _vector_store = PostgreSQLVectorStore(db_config)
            _vector_store.initialize()
        return _vector_store

    if backend == 'volcengine':
        vector_cfg = getattr(config, 'hearsight_config', {}).get('vector', {})
        volc_cfg = vector_cfg.get('volcengine', {})
        db_cfg = vector_cfg.get('database', {})  # 获取数据库配置

        from videotrans.hearsight.volcengine_vector import VolcengineVectorClient

        if not isinstance(_vector_store, VolcengineVectorClient):
            print('[vector] Using volcengine vector backend')
            print(f'[vector] PostgreSQL: {db_cfg.get("host", "未配置") if db_cfg else "未配置"}')
            _vector_store = VolcengineVectorClient(
                api_key=volc_cfg.get('api_key', ''),
                base_url=volc_cfg.get('base_url', 'https://ark.cn-beijing.volces.com/api/v3'),
                collection_name=volc_cfg.get('collection_name', 'video_summaries'),
                embedding_model=volc_cfg.get('embedding_model', ''),
                db_config=db_cfg if db_cfg else None  # 传入PostgreSQL配置
            )
        return _vector_store

    # 默认使用 chromadb
    env_dir = os.environ.get('HEARSIGHT_VECTOR_DB_DIR')
    if persist_directory is None:
        persist_directory = env_dir
    if persist_directory is None:
        hearsight_cfg = getattr(config, 'hearsight_config', {})
        vector_cfg = hearsight_cfg.get('vector', {})
        persist_directory = vector_cfg.get('persist_directory')
    if persist_directory is None:
        persist_directory = os.path.join(config.ROOT_DIR, 'vector_db')

    persist_directory = str(persist_directory)
    if not isinstance(_vector_store, VectorStore) or _vector_store.persist_directory != persist_directory:
        print('[vector] Using local ChromaDB vector backend')
        print(f'[vector] Vector DB path: {persist_directory}')
        _vector_store = VectorStore(persist_directory)
        _vector_store.initialize()

    return _vector_store

def reset_vector_store():
    """重置全局向量存储实例（用于切换后端）"""
    global _vector_store
    _vector_store = None
