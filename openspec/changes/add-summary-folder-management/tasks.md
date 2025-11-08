# Tasks: add-summary-folder-management

This file tracks implementation tasks for the folder organization feature. Complete tasks in order and mark them complete using `- [x]` when finished.

---

## Phase 1: Vector Store Backend Support

### Task 1.1: Add folder data model to vector_store.py
- [x] Define folder metadata schema (folder_id, name, created_at)
- [x] Add `folder` and `folder_id` fields to video metadata
- [x] Create `folders_registry` document structure

**Dependencies:** None
**Estimated effort:** 1 hour
**Acceptance:** Folder metadata schema defined and documented in code comments

---

### Task 1.2: Implement folder management methods in VectorStore base class
- [x] Add `create_folder(folder_name: str) -> str` method
- [x] Add `rename_folder(folder_id: str, new_name: str) -> bool` method
- [x] Add `delete_folder(folder_id: str, delete_videos: bool) -> bool` method
- [x] Add `list_folders() -> List[Dict]` method
- [x] Add `assign_video_to_folder(video_path: str, folder_id: str) -> bool` method
- [x] Add `search_in_folder(query: str, folder_id: str, n_results: int) -> List[Dict]` method

**Dependencies:** Task 1.1
**Estimated effort:** 3 hours
**Acceptance:** All methods implemented with ChromaDB backend, unit tests pass

---

### Task 1.3: Update store_summary() to accept folder parameter
- [x] Add optional `folder_id` parameter to `store_summary()` method
- [x] Default to "uncategorized" folder if not provided
- [x] Update metadata to include folder information
- [x] Test with ChromaDB backend

**Dependencies:** Task 1.2
**Estimated effort:** 1 hour
**Acceptance:** Videos can be stored with folder assignment

---

### Task 1.4: Update list_all_videos() to include folder metadata
- [x] Modify `list_all_videos()` to return `folder` and `folder_id`
- [x] Add optional `folder_id` filter parameter
- [x] Test filtering by folder

**Dependencies:** Task 1.2
**Estimated effort:** 1 hour
**Acceptance:** Video list includes folder information and can be filtered

---

### Task 1.5: Implement folder support for Qdrant backend
- [x] Implement folder methods in `QdrantVectorStoreAdapter`
- [x] Use Qdrant payload fields for folder metadata
- [x] Use `FieldCondition` for folder filtering
- [x] Test all folder operations with Qdrant

**Dependencies:** Task 1.2
**Estimated effort:** 2 hours
**Acceptance:** All folder operations work with Qdrant backend

---

### Task 1.6: Implement folder support for PostgreSQL backend
- [ ] Create `folders` table in PostgreSQL schema
- [ ] Add `folder_id` column to `transcripts` table
- [ ] Implement folder methods in `PostgreSQLVectorStore`
- [ ] Add SQL queries for folder filtering
- [ ] Test with PostgreSQL backend

**Dependencies:** Task 1.2
**Estimated effort:** 2 hours
**Acceptance:** All folder operations work with PostgreSQL backend

---

### Task 1.7: Implement folder support for Volcengine backend
- [ ] Implement folder methods in `VolcengineVectorClient`
- [ ] Store folder metadata in PostgreSQL (Volcengine doesn't store metadata)
- [ ] Implement application-layer folder filtering
- [ ] Test with Volcengine backend

**Dependencies:** Task 1.2, Task 1.6
**Estimated effort:** 2 hours
**Acceptance:** All folder operations work with Volcengine backend

---

### Task 1.8: Implement migration for existing videos
- [x] Add `_migrate_folders()` method to VectorStore
- [x] Create default "未分类" folder on first run
- [x] Assign all existing videos to default folder
- [x] Call migration in `initialize()` method
- [x] Test migration with existing data

**Dependencies:** Task 1.2
**Estimated effort:** 1 hour
**Acceptance:** Existing videos are migrated to default folder automatically

---

## Phase 2: Summary Manager UI

### Task 2.1: Add folder list panel to summary_manager.py
- [x] Create left panel with folder list (`QListWidget` or `QTreeWidget`)
- [x] Add "全部视频" pseudo-folder at top
- [x] Display folder names with video count badges
- [x] Style folder list with icons and colors
- [x] Connect folder selection to video list filtering

**Dependencies:** Task 1.4
**Estimated effort:** 2 hours
**Acceptance:** Folder list displays and clicking folder filters videos

---

### Task 2.2: Implement "New Folder" functionality
- [x] Add "New Folder" button to toolbar
- [x] Create folder name input dialog
- [x] Call `vector_store.create_folder()` on submit
- [x] Refresh folder list after creation
- [x] Show error if folder name already exists
- [x] Add keyboard shortcut (Ctrl+N)

**Dependencies:** Task 2.1
**Estimated effort:** 1.5 hours
**Acceptance:** Users can create folders with validation

---

### Task 2.3: Implement folder rename functionality
- [x] Add "Rename" option to folder context menu
- [x] Show rename dialog with current name pre-filled
- [x] Call `vector_store.rename_folder()` on submit
- [x] Refresh folder list and video list
- [x] Show error if new name already exists
- [x] Add keyboard shortcut (F2 when folder selected)

**Dependencies:** Task 2.1
**Estimated effort:** 1.5 hours
**Acceptance:** Users can rename folders with validation

---

### Task 2.4: Implement folder delete functionality
- [x] Add "Delete" option to folder context menu
- [x] Show confirmation dialog with two options:
  - "Move videos to Uncategorized"
  - "Delete folder and all videos"
- [x] Call `vector_store.delete_folder()` with appropriate flag
- [x] Refresh folder list and video list
- [x] Prevent deletion of "未分类" default folder
- [x] Add keyboard shortcut (Delete key)

**Dependencies:** Task 2.1
**Estimated effort:** 2 hours
**Acceptance:** Users can delete folders with confirmation

---

### Task 2.5: Implement video move functionality
- [x] Add "Move to Folder..." option to video context menu
- [x] Show folder selection dialog
- [x] Call `vector_store.assign_video_to_folder()` on submit
- [x] Refresh folder counts and video list
- [x] Show success confirmation

**Dependencies:** Task 2.1
**Estimated effort:** 1.5 hours
**Acceptance:** Users can move videos between folders

---

### Task 2.6: Update video list to show folder badges
- [x] Add folder name badge to each video item
- [x] Style badges with folder-specific colors (optional)
- [x] Show folder name in video detail view
- [x] Ensure badges display correctly in all view modes

**Dependencies:** Task 2.1
**Estimated effort:** 1 hour
**Acceptance:** Folder information is visible in video list

---

### Task 2.7: Update search to respect folder filtering
- [x] When folder is selected, pass `folder_id` to search
- [x] Call `vector_store.search_in_folder()` instead of `search()`
- [x] Show folder name in search results
- [x] Allow searching across all folders when "全部视频" selected

**Dependencies:** Task 2.1
**Estimated effort:** 1 hour
**Acceptance:** Search respects folder selection

---

## Phase 3: Translation UI Integration

### Task 3.1: Add folder selector to translation UI
- [ ] Add "RAG Context Folder" label and dropdown in `_main_win.py`
- [ ] Populate dropdown with folders on init using `vector_store.list_folders()`
- [ ] Add "全部视频" option (value=None) as default
- [ ] Style dropdown to match UI theme
- [ ] Store selected folder_id in instance variable

**Dependencies:** Task 1.4
**Estimated effort:** 1.5 hours
**Acceptance:** Folder selector appears in translation UI

---

### Task 3.2: Refresh folder list when translation UI opens
- [ ] Add method to reload folders from vector store
- [ ] Call reload when translation section is accessed
- [ ] Preserve selected folder if it still exists
- [ ] Fall back to "全部视频" if selected folder was deleted

**Dependencies:** Task 3.1
**Estimated effort:** 1 hour
**Acceptance:** Folder list stays current

---

### Task 3.3: Pass folder_id to translation task
- [ ] Add `rag_folder_id` field to translation task configuration
- [ ] Read selected folder_id from dropdown
- [ ] Pass to `TransCreateWorker` or task initialization
- [ ] Store in task config dict

**Dependencies:** Task 3.1
**Estimated effort:** 1 hour
**Acceptance:** Selected folder_id is passed to translation task

---

### Task 3.4: Update RAG context retrieval in trans_create.py
- [ ] Modify RAG context retrieval function to accept `folder_id` parameter
- [ ] If `folder_id` is provided, call `vector_store.search_in_folder()`
- [ ] If `folder_id` is None, call `vector_store.search()` (all videos)
- [ ] Log which folder is being used for context
- [ ] Handle case where folder no longer exists (fallback to all)

**Dependencies:** Task 3.3
**Estimated effort:** 1.5 hours
**Acceptance:** Translation uses folder-specific context when selected

---

### Task 3.5: Add folder assignment when exporting to vector store
- [ ] When Qdrant export is enabled, pass selected `folder_id`
- [ ] If no folder selected, use "uncategorized" as default
- [ ] Ensure exported video appears in correct folder in summary manager
- [ ] Test export with folder assignment

**Dependencies:** Task 1.3, Task 3.3
**Estimated effort:** 1 hour
**Acceptance:** Exported videos are assigned to correct folder

---

## Phase 4: Testing and Polish

### Task 4.1: Write unit tests for vector_store folder methods
- [ ] Test folder creation, rename, delete
- [ ] Test video-folder assignment
- [ ] Test folder filtering in search and list
- [ ] Test migration logic
- [ ] Test error handling (duplicate names, missing folders)
- [ ] Run tests on all backends (ChromaDB, Qdrant, PostgreSQL, Volcengine)

**Dependencies:** Task 1.2 - Task 1.7
**Estimated effort:** 3 hours
**Acceptance:** All unit tests pass for all backends

---

### Task 4.2: Integration testing for UI operations
- [ ] Test folder create/rename/delete flows
- [ ] Test video move operations
- [ ] Test folder filtering in summary manager
- [ ] Test folder selection in translation UI
- [ ] Test migration with existing data

**Dependencies:** Task 2.1 - Task 3.5
**Estimated effort:** 2 hours
**Acceptance:** All UI operations work end-to-end

---

### Task 4.3: Test translation with folder-specific context
- [ ] Create multiple folders with different video topics
- [ ] Test translation with folder-specific context
- [ ] Verify RAG retrieval only uses selected folder
- [ ] Test fallback when folder is deleted mid-translation
- [ ] Test with "全部视频" (all folders)

**Dependencies:** Task 3.4
**Estimated effort:** 2 hours
**Acceptance:** Folder-specific RAG context works correctly

---

### Task 4.4: Add localization strings
- [ ] Add English strings to `videotrans/language/en.json`
- [ ] Add Chinese strings to `videotrans/language/zh.json`
- [ ] Replace hardcoded strings in UI with `config.transobj[]`
- [ ] Test UI in both languages

**Dependencies:** Task 2.1 - Task 3.1
**Estimated effort:** 1 hour
**Acceptance:** All UI strings are localized

---

### Task 4.5: Performance testing
- [ ] Test with large number of folders (50+)
- [ ] Test with large number of videos per folder (100+)
- [ ] Verify folder filtering doesn't degrade search performance
- [ ] Optimize queries if needed
- [ ] Add indexes if needed (PostgreSQL)

**Dependencies:** Task 4.1 - Task 4.3
**Estimated effort:** 2 hours
**Acceptance:** Performance is acceptable with large datasets

---

### Task 4.6: Documentation and user guide
- [ ] Update CLAUDE.md with folder feature description
- [ ] Add usage examples to README or user docs
- [ ] Document folder data model and backend implementation
- [ ] Create screenshots for UI changes (optional)

**Dependencies:** Task 4.1 - Task 4.5
**Estimated effort:** 1.5 hours
**Acceptance:** Feature is documented

---

## Summary

**Total estimated effort:** ~40 hours
**Parallelizable tasks:** Phase 1 (Tasks 1.5-1.7 can run in parallel), Phase 2 (Tasks 2.2-2.5 can partially overlap)
**Critical path:** Task 1.2 → Task 2.1 → Task 3.1 → Task 3.4
**Validation checkpoints:**
- After Task 1.2: Verify folder backend works
- After Task 2.1: Verify UI displays folders
- After Task 3.4: Verify translation uses folder context
- After Task 4.3: Full end-to-end validation
