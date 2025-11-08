# Spec: Summary Folder Organization

## Overview
This spec defines the folder organization capability for the video summary library (HearSight), enabling users to organize videos into folders and use folder-based context filtering during translation.

---

## ADDED Requirements

### Requirement: SFO-001 — Folder Creation and Management

Users must be able to create, rename, and delete folders in the summary library.

#### Scenario: Creating a new folder
**Given** the user opens the summary manager
**When** the user clicks "New Folder" and enters "Tech Tutorials"
**Then** a new folder "Tech Tutorials" appears in the folder list
**And** the folder has 0 videos initially

#### Scenario: Renaming a folder
**Given** a folder "Tech" exists
**When** the user right-clicks the folder and selects "Rename"
**And** enters "Tech Tutorials"
**Then** the folder name updates to "Tech Tutorials"
**And** all videos in the folder remain assigned to it

#### Scenario: Deleting an empty folder
**Given** a folder "Old Folder" exists with 0 videos
**When** the user right-clicks and selects "Delete"
**Then** the folder is removed from the list

#### Scenario: Deleting a folder with videos
**Given** a folder "Tech" exists with 3 videos
**When** the user right-clicks and selects "Delete"
**Then** a confirmation dialog appears with options:
  - "Move videos to Uncategorized"
  - "Delete folder and all videos"
**When** the user selects "Move videos to Uncategorized"
**Then** the folder is deleted
**And** all 3 videos are moved to "未分类" folder

---

### Requirement: SFO-002 — Video-Folder Assignment

Users must be able to assign videos to folders.

#### Scenario: Moving a video to a folder
**Given** a video "Tutorial.mp4" is in "未分类" folder
**And** a folder "Tech Tutorials" exists
**When** the user right-clicks the video and selects "Move to Folder > Tech Tutorials"
**Then** the video moves to "Tech Tutorials" folder
**And** the video disappears from "未分类" folder list
**And** "Tech Tutorials" folder shows video count +1

#### Scenario: Moving a video from one folder to another
**Given** a video "Meeting.mp4" is in "Business" folder
**When** the user moves it to "Archive" folder
**Then** "Business" folder video count decreases by 1
**And** "Archive" folder video count increases by 1

#### Scenario: Assigning folder during translation export
**Given** a user completes video translation with Qdrant export enabled
**And** the translation UI has folder selector set to "Tech Tutorials"
**When** the export completes
**Then** the video summary is stored with folder_id="tech_tutorials"
**And** the video appears in "Tech Tutorials" folder in summary manager

---

### Requirement: SFO-003 — Folder-Based Video Filtering

The summary manager must display videos filtered by selected folder.

#### Scenario: Viewing all videos
**Given** the summary manager is open
**When** the user selects "全部视频" (All Videos) folder
**Then** all videos from all folders are displayed in the video list
**And** each video shows its folder name as a badge

#### Scenario: Filtering by folder
**Given** folders exist: "Tech" (3 videos), "Business" (2 videos)
**When** the user clicks "Tech" folder
**Then** only the 3 videos from "Tech" folder are displayed
**And** videos from other folders are hidden

#### Scenario: Empty folder display
**Given** a folder "Empty Folder" exists with 0 videos
**When** the user clicks "Empty Folder"
**Then** the video list shows "此文件夹为空" (This folder is empty)

---

### Requirement: SFO-004 — Default Folder Handling

The system must provide a default "未分类" (Uncategorized) folder.

#### Scenario: First launch after update (migration)
**Given** existing videos have no folder metadata
**When** the user opens summary manager for the first time
**Then** a default "未分类" folder is created automatically
**And** all existing videos are assigned to "未分类" folder
**And** the migration completes silently without user action

#### Scenario: New video without folder assignment
**Given** a user translates a new video
**And** no folder is selected in the translation UI
**When** the summary is exported to vector store
**Then** the video is assigned to "未分类" folder by default

#### Scenario: Deleting the default folder
**Given** the "未分类" folder exists
**When** the user attempts to delete it
**Then** the delete action is prevented
**And** a message shows "无法删除默认文件夹" (Cannot delete default folder)

---

### Requirement: SFO-005 — Folder Selection in Translation UI

Users must be able to select a folder to use for RAG context during translation.

#### Scenario: Selecting folder for RAG context
**Given** the translation UI is open
**And** folders exist: "Tech", "Business", "未分类"
**When** the user expands the "RAG Context Folder" dropdown
**Then** the dropdown shows:
  - "全部视频" (All Videos) — default
  - "未分类" (Uncategorized)
  - "Tech"
  - "Business"

#### Scenario: Translation with folder-specific context
**Given** the user selects "Tech" folder in RAG context dropdown
**And** starts translating a video about programming
**When** the translation task retrieves RAG context
**Then** only summaries from videos in "Tech" folder are used
**And** videos from "Business" or "未分类" are excluded from context

#### Scenario: Translation with all videos context
**Given** the user selects "全部视频" in RAG context dropdown
**When** the translation task retrieves RAG context
**Then** summaries from all folders are used for context

---

### Requirement: SFO-006 — Folder Metadata Persistence

Folder information must persist across all supported vector backends.

#### Scenario: Storing folder metadata in ChromaDB
**Given** the system uses ChromaDB backend
**When** a video is assigned to "Tech" folder
**Then** the video metadata includes:
  - `folder`: "Tech"
  - `folder_id`: "tech_123"
**And** searching within "Tech" folder filters by `where={"folder_id": "tech_123"}`

#### Scenario: Storing folder metadata in Qdrant
**Given** the system uses Qdrant backend
**When** a video is assigned to "Business" folder
**Then** the point payload includes:
  - `folder`: "Business"
  - `folder_id`: "business_456"
**And** folder filtering uses `FieldCondition(key="folder_id", match=MatchValue(value="business_456"))`

#### Scenario: Storing folder metadata in PostgreSQL
**Given** the system uses PostgreSQL backend
**When** a video is assigned to "Archive" folder
**Then** a record is created in the `folders` table
**And** the `transcripts` table row includes `folder_id` foreign key
**And** folder filtering uses SQL `WHERE folder_id = 'archive_789'`

#### Scenario: Folder registry persistence
**Given** folders "Tech", "Business", "Archive" are created
**When** the application restarts
**Then** all 3 folders are loaded from the folders_registry document
**And** video counts are recalculated from video metadata

---

### Requirement: SFO-007 — Folder List Display

The summary manager must display folders with accurate video counts.

#### Scenario: Displaying folder list
**Given** folders exist:
  - "未分类" (5 videos)
  - "Tech Tutorials" (3 videos)
  - "Business Meetings" (2 videos)
**When** the summary manager loads
**Then** the folder list displays:
  ```
  📁 全部视频 (10)
  📁 未分类 (5)
  📁 Tech Tutorials (3)
  📁 Business Meetings (2)
  ```

#### Scenario: Updating folder count after video move
**Given** "Tech" folder has 3 videos
**When** a video is moved from "Tech" to "Business"
**Then** "Tech" folder count updates to 2
**And** "Business" folder count increases by 1
**And** the UI reflects the new counts without requiring refresh

---

### Requirement: SFO-008 — Folder Search Isolation

Semantic search within a folder must only return results from that folder.

#### Scenario: Searching within a folder
**Given** videos exist:
  - "Python Tutorial" in "Tech" folder
  - "Python for Business" in "Business" folder
**And** the user is viewing "Tech" folder
**When** the user searches for "Python"
**Then** only "Python Tutorial" appears in search results
**And** "Python for Business" is excluded

#### Scenario: Searching across all folders
**Given** the user selects "全部视频" folder
**When** the user searches for "Python"
**Then** both "Python Tutorial" and "Python for Business" appear in results
**And** each result shows its folder name

---

### Requirement: SFO-009 — Error Handling for Folder Operations

The system must handle folder operation errors gracefully.

#### Scenario: Creating duplicate folder name
**Given** a folder "Tech" already exists
**When** the user tries to create another folder named "Tech"
**Then** an error message shows "文件夹名称已存在" (Folder name already exists)
**And** the folder is not created

#### Scenario: Renaming to existing folder name
**Given** folders "Tech" and "Business" exist
**When** the user tries to rename "Tech" to "Business"
**Then** an error message shows "文件夹名称已存在"
**And** the rename operation is cancelled

#### Scenario: Moving video when target folder doesn't exist
**Given** a video has folder_id="deleted_folder"
**And** that folder no longer exists in folders_registry
**When** the summary manager loads
**Then** the video is automatically reassigned to "未分类" folder
**And** a warning is logged: "Folder 'deleted_folder' not found, moved to Uncategorized"

#### Scenario: Translation with deleted folder selected
**Given** the user selected "Tech" folder for RAG context
**And** starts a translation task
**When** "Tech" folder is deleted before translation completes
**Then** the translation falls back to "全部视频" context
**And** a warning shows: "Selected folder no longer exists, using all videos"

---

## MODIFIED Requirements

_None (this is a new feature)_

---

## REMOVED Requirements

_None_
