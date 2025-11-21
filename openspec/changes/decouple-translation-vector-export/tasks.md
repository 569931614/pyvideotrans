# Tasks: decouple-translation-vector-export

## 1. Core Service Layer
- [ ] 1.1 Create `videotrans/service/` directory
- [ ] 1.2 Implement `VectorExportService` class with:
  - [ ] 1.2.1 `export_from_task()` method (for auto-export during translation)
  - [ ] 1.2.2 `export_from_files()` method (for manual export from UI)
  - [ ] 1.2.3 `batch_export()` method (for batch manual export)
  - [ ] 1.2.4 Progress callback support (for UI progress bars)
  - [ ] 1.2.5 OSS upload integration (call `OSSUploader` if needed)
  - [ ] 1.2.6 Error handling and retry logic
- [ ] 1.3 Add unit tests for `VectorExportService`

## 2. Update Translation Tasks (Make Export Optional)
- [ ] 2.1 Update `videotrans/task/trans_create.py`:
  - [ ] 2.1.1 Replace inline `_export_to_qdrant()` with call to `VectorExportService.export_from_task()`
  - [ ] 2.1.2 Check `config.params.get('qdrant_auto_export', False)` before calling
  - [ ] 2.1.3 Show notification after translation with link to Vector Export Manager
- [ ] 2.2 Update `videotrans/task/_translate_srt.py`:
  - [ ] 2.2.1 Replace inline `_export_to_qdrant()` with call to `VectorExportService.export_from_task()`
  - [ ] 2.2.2 Check `config.params.get('qdrant_auto_export', False)` before calling
  - [ ] 2.2.3 Show notification after translation

## 3. Vector Export Manager UI
- [ ] 3.1 Create `videotrans/ui/vector_export_manager.py`:
  - [ ] 3.1.1 Design UI layout (file browser, options, preview, progress)
  - [ ] 3.1.2 Implement file selection (video + SRT pairs)
  - [ ] 3.1.3 Add batch file selection support
  - [ ] 3.1.4 Implement OSS upload checkbox and integration
  - [ ] 3.1.5 Implement folder selector (dropdown + "New Folder" button)
  - [ ] 3.1.6 Implement metadata preview panel
  - [ ] 3.1.7 Implement progress bars (per-video and overall)
  - [ ] 3.1.8 Wire up "Export to Vector DB" button to `VectorExportService.batch_export()`
  - [ ] 3.1.9 Add error handling and user-friendly error messages
  - [ ] 3.1.10 Add duplicate detection (warn if video_id exists in Qdrant)
- [ ] 3.2 Add menu item in `videotrans/mainwin/_main_win.py`:
  - [ ] 3.2.1 Add "Summary Library" → "Upload to Vector Database" menu item
  - [ ] 3.2.2 Connect menu item to open Vector Export Manager UI

## 4. Update Translation UI (Auto-Export Checkbox)
- [ ] 4.1 Add auto-export checkbox to translation UI:
  - [ ] 4.1.1 Add "☐ Auto-export to vector database after translation" checkbox
  - [ ] 4.1.2 Store preference in `config.params['qdrant_auto_export']`
  - [ ] 4.1.3 Load preference on UI initialization
- [ ] 4.2 Update translation settings dialog (if separate from main UI)

## 5. Configuration Migration
- [ ] 5.1 Update `videotrans/configure/_config_loader.py`:
  - [ ] 5.1.1 Add migration logic: `qdrant_enabled` → `qdrant_auto_export`
  - [ ] 5.1.2 Default `qdrant_auto_export` to `False` for new users
  - [ ] 5.1.3 Log migration for debugging
- [ ] 5.2 Update config schema documentation (if exists)

## 6. Update Vector Metadata Schema
- [ ] 6.1 Update `videotrans/qdrant_export/qdrant_client.py`:
  - [ ] 6.1.1 Add `oss_url` field to `VideoMetadata` dataclass
  - [ ] 6.1.2 Add `upload_timestamp` field to `VideoMetadata` dataclass
  - [ ] 6.1.3 Update `source_type` to support "pyvideotrans_oss" value
  - [ ] 6.1.4 Ensure backward compatibility with existing metadata
- [ ] 6.2 Update `videotrans/qdrant_export/export.py`:
  - [ ] 6.2.1 Accept optional `oss_url` parameter
  - [ ] 6.2.2 Populate `oss_url` in metadata if provided

## 7. OSS Integration
- [ ] 7.1 Ensure `OSSUploader` supports progress callbacks (already exists)
- [ ] 7.2 Add retry logic for failed OSS uploads (already exists)
- [ ] 7.3 Test OSS upload with large files (100MB+)

## 8. Testing
- [ ] 8.1 Unit tests:
  - [ ] 8.1.1 Test `VectorExportService.export_from_files()` with local paths
  - [ ] 8.1.2 Test `VectorExportService.export_from_files()` with OSS URLs
  - [ ] 8.1.3 Test config migration logic
- [ ] 8.2 Integration tests:
  - [ ] 8.2.1 End-to-end: Translate → Manual export → Verify Qdrant
  - [ ] 8.2.2 End-to-end: Translate with auto-export → Verify Qdrant
  - [ ] 8.2.3 End-to-end: OSS upload → Vector export → Verify metadata
- [ ] 8.3 Manual testing:
  - [ ] 8.3.1 Test Vector Export Manager UI workflow
  - [ ] 8.3.2 Test batch upload (multiple videos)
  - [ ] 8.3.3 Test error cases (invalid SRT, missing video, OSS failure)
  - [ ] 8.3.4 Test duplicate detection and warning

## 9. Documentation
- [ ] 9.1 Update `CLAUDE.md` with new workflow:
  - [ ] 9.1.1 Document Vector Export Manager usage
  - [ ] 9.1.2 Document auto-export configuration
  - [ ] 9.1.3 Document OSS integration
- [ ] 9.2 Add user-facing help text in UI (tooltips, info buttons)
- [ ] 9.3 Update any existing README or user guide

## 10. Polish and Error Handling
- [ ] 10.1 Add progress notifications:
  - [ ] 10.1.1 "Uploading to OSS... (X%)"
  - [ ] 10.1.2 "Generating embeddings... (X/Y chunks)"
  - [ ] 10.1.3 "Uploading to Qdrant..."
- [ ] 10.2 Add user-friendly error messages:
  - [ ] 10.2.1 OSS upload failures
  - [ ] 10.2.2 Qdrant connection errors
  - [ ] 10.2.3 Invalid file selections (missing SRT, wrong format)
- [ ] 10.3 Add first-launch notification about new feature
- [ ] 10.4 Ensure proper resource cleanup (threads, file handles)
