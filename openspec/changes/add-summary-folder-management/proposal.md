# Proposal: add-summary-folder-management

## Summary
Add folder organization capability to the video summary library (HearSight), allowing users to organize videos into folders and select folders during translation for context-aware RAG.

## Problem Statement
Currently, the summary library displays all videos in a flat list without organization. As users accumulate more translated videos, it becomes difficult to:
- Organize videos by topic, project, or category
- Find relevant videos when browsing the library
- Select relevant videos for context-aware translation

## Proposed Solution
Implement a folder/category system for organizing video summaries:

1. **Folder Management in Summary Library**
   - Add UI to create, rename, and delete folders
   - Allow users to assign videos to folders (move, copy)
   - Display videos in a hierarchical folder tree or filtered by folder

2. **Folder Selection During Translation**
   - Add folder selector in the translation UI
   - When translating, use only summaries from selected folder(s) for RAG context
   - Improve translation relevance by limiting context to related videos

## User Stories

### As a user organizing video summaries
- I want to create folders (e.g., "Tech Tutorials", "Business Meetings", "Educational")
- I want to move videos between folders
- I want to view videos filtered by folder

### As a user translating videos
- I want to select which folder's summaries to use as context
- I want translations to use only relevant previous videos
- I want the option to use all videos or folder-specific context

## Acceptance Criteria
- [ ] Users can create/rename/delete folders in the summary manager
- [ ] Users can assign videos to folders (with UI drag-drop or context menu)
- [ ] Summary library displays videos grouped by folder
- [ ] Translation UI includes folder selector for RAG context
- [ ] Translations use only selected folder's summaries as context
- [ ] Folder metadata persists in vector database
- [ ] All folder operations work with current vector backends (Qdrant, ChromaDB, PostgreSQL, Volcengine)

## Out of Scope
- Multi-folder selection for translation (single folder only in v1)
- Nested folders (flat folder structure only)
- Folder sharing or permissions
- Automatic folder suggestion based on video content

## Dependencies
- Requires existing summary library (`videotrans/ui/summary_manager.py`)
- Requires vector store abstraction (`videotrans/hearsight/vector_store.py`)
- Requires translation workflow (`videotrans/task/trans_create.py`)

## Risks
- **Vector Backend Compatibility**: All vector backends must support folder metadata filtering
- **Migration**: Existing videos in database need default folder assignment
- **Performance**: Folder filtering must not degrade search performance
