# Design: Folder Organization for Video Summary Library

## Architecture Overview

The folder system will be implemented across three layers:

1. **Data Layer** (`vector_store.py`): Store folder metadata with video summaries
2. **UI Layer** (`summary_manager.py`): Folder management interface in summary library
3. **Integration Layer** (`trans_create.py`, `_main_win.py`): Folder selection during translation

## Data Model

### Folder Metadata Structure
Each video summary will include folder metadata:

```python
{
    "video_id": "abc123...",
    "video_path": "/path/to/video.mp4",
    "folder": "Tech Tutorials",  # NEW: folder name (default: "未分类" / "Uncategorized")
    "folder_id": "folder_123",   # NEW: unique folder identifier
    "type": "overall_summary",
    # ... existing metadata
}
```

### Folder Registry
A special collection document will store folder definitions:

```python
{
    "id": "folders_registry",
    "type": "folder_registry",
    "folders": [
        {
            "folder_id": "folder_123",
            "name": "Tech Tutorials",
            "created_at": "2025-01-07T10:00:00",
            "video_count": 5
        },
        # ...
    ]
}
```

## Component Changes

### 1. Vector Store (`videotrans/hearsight/vector_store.py`)

**New Methods:**
- `create_folder(folder_name: str) -> str`: Create folder, return folder_id
- `rename_folder(folder_id: str, new_name: str) -> bool`: Rename folder
- `delete_folder(folder_id: str, delete_videos: bool = False) -> bool`: Delete folder
- `list_folders() -> List[Dict]`: Get all folders with video counts
- `assign_video_to_folder(video_path: str, folder_id: str) -> bool`: Move video to folder
- `search_in_folder(query: str, folder_id: str, n_results: int) -> List[Dict]`: Search within folder

**Modified Methods:**
- `store_summary()`: Accept optional `folder_id` parameter (default: "uncategorized")
- `list_all_videos()`: Include `folder` and `folder_id` in returned data
- `get_video_summary()`: Include folder metadata

**Backend Compatibility:**
All backends (Qdrant, ChromaDB, PostgreSQL, Volcengine) must implement folder support:
- **ChromaDB**: Use metadata fields `folder` and `folder_id`, filter with `where` clauses
- **Qdrant**: Use payload fields, filter with `FieldCondition`
- **PostgreSQL**: Add `folder_id` column to transcripts table, join with folders table
- **Volcengine**: Store folder in metadata, filter in application layer

### 2. Summary Manager UI (`videotrans/ui/summary_manager.py`)

**New UI Components:**
```
┌─────────────────────────────────────────────────────────┐
│  HearSight - 摘要管理                                     │
├─────────────────────────────────────────────────────────┤
│  [刷新] [新建文件夹]                                       │
├───────────┬─────────────────────────────────────────────┤
│ 文件夹列表 │ 视频列表                │ 详情               │
│           │                        │                   │
│ 📁 全部    │ [视频] Example.mp4     │ [整体摘要]         │
│ 📁 未分类  │ [段落] 3段 | [时长]... │ ...               │
│ 📁 Tech   │ [视频] Tutorial.mp4    │ [段落详情]         │
│ 📁 Business│ ...                    │ ...               │
│           │                        │                   │
└───────────┴────────────────────────┴───────────────────┘
```

**New Features:**
- Left panel: Folder tree/list with video counts
- Context menu on folders: Rename, Delete
- Context menu on videos: Move to Folder...
- "New Folder" button in toolbar
- Clicking folder filters video list
- "All Videos" pseudo-folder shows unfiltered view

**Implementation:**
- Use `QTreeWidget` or `QListWidget` for folder list
- Use `QMenu` for context menus
- Add dialog for creating/renaming folders
- Add move dialog with folder dropdown

### 3. Translation UI Integration (`videotrans/mainwin/_main_win.py`)

**New UI Element:**
Add folder selector near translation settings:

```python
# In translation section
self.rag_folder_label = QLabel("RAG上下文文件夹:")
self.rag_folder_combo = QComboBox()
self.rag_folder_combo.addItem("全部视频", None)  # Show all
self.rag_folder_combo.addItem("未分类", "uncategorized")
# ... populate with user folders

layout.addWidget(self.rag_folder_label)
layout.addWidget(self.rag_folder_combo)
```

**Behavior:**
- Loads folders on init (via `vector_store.list_folders()`)
- Stores selected folder_id in translation task config
- Passes folder_id to RAG context retrieval

### 4. Translation Task (`videotrans/task/trans_create.py`)

**Modified RAG Context Retrieval:**

```python
# In get_rag_context() or similar
def get_rag_context(self, query: str):
    vector_store = get_vector_store()
    folder_id = self.task_config.get('rag_folder_id')  # NEW

    if folder_id:
        # Search only in selected folder
        results = vector_store.search_in_folder(query, folder_id, n_results=5)
    else:
        # Search all videos
        results = vector_store.search(query, n_results=5)

    # ... format context
```

## Migration Strategy

### Existing Data
On first load after update:
1. Check if folders_registry exists
2. If not, create default "未分类" folder
3. Assign all existing videos to "未分类" folder
4. Update all video metadata with folder_id

### Migration Code
Add to `vector_store.initialize()`:

```python
def _migrate_folders(self):
    """Migrate existing videos to folder system"""
    try:
        # Check if migration needed
        folders = self.list_folders()
        if not folders:
            # Create default folder
            default_id = self.create_folder("未分类")

            # Assign all videos to default folder
            videos = self.list_all_videos()
            for video in videos:
                self.assign_video_to_folder(video['video_path'], default_id)

            print(f"[Migration] Migrated {len(videos)} videos to default folder")
    except Exception as e:
        print(f"[Migration] Warning: {e}")
```

## Performance Considerations

### Indexing
- All vector backends already support metadata filtering
- ChromaDB/Qdrant: Folder filtering is O(1) with metadata indexes
- PostgreSQL: Add index on `folder_id` column

### Caching
- Cache folder list in UI (refresh on demand)
- Don't reload folders on every translation start

### Search
- Folder filtering should not significantly impact search speed
- Most backends support efficient filtered queries

## Error Handling

### Folder Deletion
- **Delete folder only**: Move videos to "未分类"
- **Delete folder + videos**: Confirm dialog, cascade delete

### Video Move
- Validate folder_id exists before moving
- If folder doesn't exist, fallback to "未分类"

### Translation
- If selected folder is deleted, fallback to all videos
- Show warning in UI if folder no longer exists

## Testing Strategy

1. **Unit Tests**: Test vector_store folder methods with each backend
2. **Integration Tests**: Test UI operations (create, rename, delete, move)
3. **Migration Tests**: Test migration with existing data
4. **Translation Tests**: Verify folder filtering in RAG context

## UI/UX Considerations

### Defaults
- New videos default to "未分类" folder
- Translation defaults to "全部视频" (no folder filter)

### Visual Feedback
- Show video count badges on folders
- Highlight selected folder
- Show folder name in video list items

### Accessibility
- Keyboard shortcuts for folder operations (Ctrl+N: new folder, F2: rename)
- Keyboard navigation in folder list

## Localization
All UI strings support English and Chinese:
- "未分类" / "Uncategorized"
- "全部视频" / "All Videos"
- "新建文件夹" / "New Folder"
- "移动到文件夹" / "Move to Folder"
- "RAG上下文文件夹" / "RAG Context Folder"
