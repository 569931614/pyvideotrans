# Proposal: decouple-translation-vector-export

## Summary
Decouple video translation from vector database export, allowing users to:
1. Translate videos and save locally without automatic vector export
2. Separately upload translated videos to OSS and vector database through a dedicated UI

## Why
Currently, Qdrant vector export is tightly coupled with the translation workflow:
- After translation completes, it automatically exports to Qdrant if enabled
- Users cannot control when/whether to upload to vector database
- No way to upload already-translated videos to vector database later
- OSS upload exists but is not integrated with vector export workflow

This creates inflexibility:
- Users may want to review translations before uploading to vector DB
- Batch uploading multiple videos requires re-translation
- Cannot organize videos into folders before upload
- Automatic upload can fail silently during translation, requiring re-translation

## What Changes
1. **Make vector export optional during translation**
   - Add checkbox in translation UI: "Auto-export to vector database after translation"
   - Default: disabled (breaking change from current auto-export behavior)
   - Store preference in config

2. **Create dedicated "Vector Export Manager" UI**
   - New menu item: "Summary Library" → "Upload to Vector Database"
   - Browse and select local translated video files + SRT
   - Optional: Upload video file to OSS first
   - Select folder for organization
   - Preview metadata before upload
   - Batch upload support

3. **Integrate OSS upload with vector export**
   - When exporting to vector DB, offer OSS upload option
   - If uploaded to OSS, store OSS URL in vector metadata
   - Otherwise, store local file path

4. **Refactor export code for reusability**
   - Extract `_export_to_qdrant()` from task classes into shared utility
   - Create `VectorExportService` class handling both auto and manual export
   - Support standalone invocation with video path + SRT path

## Impact

### Affected code:
- `videotrans/task/trans_create.py:792-878` - Remove or make optional auto-export
- `videotrans/task/_translate_srt.py:101-159` - Remove or make optional auto-export
- `videotrans/qdrant_export/export.py` - Refactor for standalone use
- **NEW**: `videotrans/ui/vector_export_manager.py` - New UI for manual export
- **NEW**: `videotrans/service/vector_export_service.py` - Shared export logic
- `videotrans/mainwin/_main_win.py` - Add menu item for Vector Export Manager
- `videotrans/util/oss_uploader.py` - Integrate with vector export

### Affected specs:
- Translation workflow (optional vector export)
- Vector database integration (decoupled from translation)
- OSS upload (integrated with vector export)

### Breaking changes:
- **BREAKING**: Auto-export to vector database after translation is now disabled by default
- Users who rely on automatic export must explicitly enable the checkbox

## Out of Scope
- Modifying existing vector database records (edit/delete) - future work
- Automatic folder suggestion based on video content
- Multi-vector-backend support in one session (remains single backend)

## Dependencies
- Existing `videotrans/qdrant_export/` module
- Existing `videotrans/util/oss_uploader.py` module
- Existing `videotrans/hearsight/vector_store.py` abstraction
- Translation workflow (`videotrans/task/trans_create.py`, `videotrans/task/_translate_srt.py`)

## Risks
- **User confusion**: Existing users expect auto-export behavior
  - *Mitigation*: Add clear UI notification after translation completes, showing link to Vector Export Manager
- **Config migration**: Need to handle existing `qdrant_enabled` config
  - *Mitigation*: Rename to `qdrant_auto_export` for clarity, auto-migrate old config
- **Code duplication**: Export logic used in both auto and manual flows
  - *Mitigation*: Extract into shared `VectorExportService` class
