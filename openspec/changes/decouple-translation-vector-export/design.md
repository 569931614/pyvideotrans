# Design: decouple-translation-vector-export

## Context
Currently, vector database export (Qdrant) is automatically triggered after translation completes. This design decouples the two operations, providing users with:
1. Control over when/whether to export to vector database
2. Ability to upload existing translated videos
3. Integration with OSS upload for cloud storage
4. Folder organization during upload

## Goals
- Decouple translation completion from vector export
- Provide dedicated UI for manual vector database upload
- Integrate OSS upload seamlessly with vector export
- Maintain backward compatibility where reasonable

## Non-Goals
- Editing/deleting existing vector database entries (future work)
- Supporting multiple vector backends simultaneously in one session
- Automatic content-based folder suggestion

## Architecture

### Current Flow (Tightly Coupled)
```
Translation Task
    ↓
task_done()
    ↓
_export_to_qdrant() [automatic, non-optional]
    ↓
export_to_qdrant() from videotrans.qdrant_export
    ↓
Qdrant + local file path
```

### Proposed Flow (Decoupled)

**Flow 1: Translation (Optional Export)**
```
Translation Task
    ↓
task_done()
    ↓
IF user enabled "Auto-export to vector DB":
    ↓
    VectorExportService.export_from_task()
    ↓
    Qdrant + local file path
ELSE:
    ↓
    Show notification: "Translation complete. Upload to vector DB anytime via Summary Library."
```

**Flow 2: Manual Export (New)**
```
User opens Vector Export Manager UI
    ↓
Select video file(s) + corresponding SRT file(s)
    ↓
[Optional] Upload video to OSS
    ↓
Select folder for organization
    ↓
Preview metadata (title, duration, chunks, language)
    ↓
Click "Upload to Vector Database"
    ↓
VectorExportService.export_from_files()
    ↓
Qdrant + OSS URL (if uploaded) or local path
```

### Component Design

#### 1. VectorExportService (New)
**Location**: `videotrans/service/vector_export_service.py`

**Responsibilities**:
- Centralize vector export logic (previously in task classes)
- Support both automatic (during translation) and manual (from UI) export
- Handle OSS upload integration
- Provide progress callbacks for UI

**Public API**:
```python
class VectorExportService:
    def export_from_task(
        task_config: Dict,
        srt_path: str,
        video_path: str,
        progress_callback: Optional[Callable] = None
    ) -> ExportResult

    def export_from_files(
        video_file: str,
        srt_file: str,
        folder_id: Optional[str] = None,
        upload_to_oss: bool = False,
        oss_config: Optional[Dict] = None,
        export_config: ExportConfig,
        progress_callback: Optional[Callable] = None
    ) -> ExportResult

    def batch_export(
        items: List[ExportItem],
        export_config: ExportConfig,
        progress_callback: Optional[Callable] = None
    ) -> List[ExportResult]
```

#### 2. Vector Export Manager UI (New)
**Location**: `videotrans/ui/vector_export_manager.py`

**Features**:
- File browser for selecting video + SRT pairs
- Batch selection support (multiple videos)
- OSS upload checkbox + progress bar
- Folder selector (dropdown from existing folders or create new)
- Metadata preview (auto-populated from SRT)
- Progress display (per-video and overall)
- Error handling and retry

**UI Layout**:
```
┌─────────────────────────────────────────────┐
│ Vector Export Manager                        │
├─────────────────────────────────────────────┤
│ Select Files:                                │
│ ┌─────────────────────────────────────────┐ │
│ │ Video: output_translated.mp4            │ │
│ │ SRT:   output_translated.zh-cn.srt      │ │
│ └─────────────────────────────────────────┘ │
│ [Add More Files] [Clear Selection]          │
│                                              │
│ Options:                                     │
│ ☐ Upload video to OSS                       │
│ Folder: [Select Folder ▼] [New Folder]      │
│                                              │
│ Export Configuration:                        │
│ ☑ Generate summaries                        │
│ LLM: [deepseek-ai/DeepSeek-V3  ▼]          │
│ Embedding: [BAAI/bge-large-zh-v1.5 ▼]      │
│                                              │
│ Preview (2 videos selected):                 │
│ • video1.mp4 (zh-cn, 120 chunks, 5.2MB)     │
│ • video2.mp4 (en, 85 chunks, 3.1MB)         │
│                                              │
│ [Cancel]              [Export to Vector DB]  │
└─────────────────────────────────────────────┘
```

#### 3. Updated Translation UI
**Location**: `videotrans/mainwin/_main_win.py` (or relevant translation dialog)

**Changes**:
- Add checkbox: "☐ Auto-export to vector database after translation"
- Show in Settings or Translation form
- Store preference in `config.params['qdrant_auto_export']`

#### 4. Updated Task Classes
**Locations**:
- `videotrans/task/trans_create.py`
- `videotrans/task/_translate_srt.py`

**Changes**:
- Replace inline `_export_to_qdrant()` with call to `VectorExportService.export_from_task()`
- Check `config.params.get('qdrant_auto_export', False)` before exporting
- Show notification after translation: "Translation complete. Upload to vector DB via Summary Library → Vector Export Manager."

## Data Flow

### OSS Upload Integration

**Scenario 1: Upload to OSS, then export to vector DB**
```
video.mp4 (local)
    ↓
OSSUploader.upload_file()
    ↓
OSS URL: https://bucket.oss.com/videos/2025-11-21/abc123_video.mp4
    ↓
VectorExportService.export_from_files(video_url=oss_url)
    ↓
Qdrant metadata: {
    video_path: "https://bucket.oss.com/...",
    source_type: "pyvideotrans_oss"
}
```

**Scenario 2: Export to vector DB with local path only**
```
video.mp4 (local)
    ↓
VectorExportService.export_from_files(video_url=local_path)
    ↓
Qdrant metadata: {
    video_path: "F:/videos/output/video.mp4",
    source_type: "pyvideotrans"
}
```

### Metadata Schema (Qdrant)

```python
VideoMetadata = {
    "video_id": str,              # SHA-256 hash
    "video_title": str,
    "video_path": str,            # Local path or OSS URL
    "source_type": str,           # "pyvideotrans" or "pyvideotrans_oss"
    "language": str,
    "duration": float,
    "chunk_count": int,
    "video_summary": str,
    "keywords": List[str],
    "srt_file": str,              # Local SRT path (for reference)
    "folder_id": Optional[str],
    "folder": Optional[str],      # Folder name
    "oss_url": Optional[str],     # Explicit OSS URL field (new)
    "upload_timestamp": int       # Unix timestamp (new)
}
```

## Decisions

### Decision 1: Auto-export disabled by default
**Rationale**:
- Gives users explicit control
- Prevents accidental uploads during testing
- Allows review before upload

**Alternatives considered**:
- Keep auto-export enabled by default: Rejected due to user surprise factor
- Remove auto-export entirely: Rejected to maintain workflow efficiency for power users

### Decision 2: Reuse existing `qdrant_export` module
**Rationale**:
- Proven, working implementation
- No need to rewrite SRT parsing, chunking, summarization
- Focus changes on orchestration layer

**Alternatives considered**:
- Rewrite export module: Rejected as unnecessary refactoring

### Decision 3: OSS upload as optional pre-step
**Rationale**:
- Users may want local-only vector DB (dev/testing)
- Separates concerns (storage vs. indexing)
- Provides flexibility

**Alternatives considered**:
- Always upload to OSS: Rejected due to inflexibility
- Make OSS URL mandatory: Rejected for same reason

### Decision 4: Keep folder management in existing UI
**Rationale**:
- Folder CRUD is already handled by Summary Manager
- Vector Export Manager focuses on upload operation
- Reduces scope and complexity

**Alternatives considered**:
- Add folder management to Vector Export Manager: Rejected to avoid duplication

## Migration Plan

### Config Migration
**Old config** (`set.ini` or `cfg.json`):
```json
{
    "qdrant_enabled": true
}
```

**New config**:
```json
{
    "qdrant_auto_export": false,  // Default: disabled
    "qdrant_enabled": true         // Keep for backward compat (read-only)
}
```

**Migration logic** (in `_config_loader.py`):
```python
if 'qdrant_enabled' in params and 'qdrant_auto_export' not in params:
    params['qdrant_auto_export'] = params['qdrant_enabled']
    logger.info("Migrated qdrant_enabled to qdrant_auto_export")
```

### User Communication
1. **First launch notification** (after update):
   - "New feature: Manual vector database upload now available! Auto-export is disabled by default. Enable in Settings → Vector Database → Auto-export after translation."

2. **Post-translation notification**:
   - "Translation complete! Upload to vector database anytime via Summary Library → Vector Export Manager."

### Rollback Plan
If issues arise:
1. Set `qdrant_auto_export = true` in config to restore old behavior
2. Hide "Vector Export Manager" menu item via feature flag

## Open Questions
1. **Q**: Should we support editing existing vector DB entries?
   - **A**: Out of scope for this change. Future enhancement.

2. **Q**: Should OSS upload be background/async?
   - **A**: Yes. Use threading with progress callback (similar to existing task system).

3. **Q**: How to handle duplicate uploads (same video)?
   - **A**: Warn user if `video_id` already exists in Qdrant. Offer "Skip" or "Overwrite" options.

4. **Q**: Should we validate video file exists before export?
   - **A**: Yes. Check both video and SRT files exist and are readable before starting.

## Risks and Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Users don't notice new UI | Medium | Medium | Add prominent notification after translation |
| Broken backward compat | High | Low | Config migration + keep old `qdrant_enabled` working |
| OSS upload failure | Medium | Medium | Retry logic + clear error messages |
| Vector DB quota exceeded | Low | Low | Catch and display quota errors from Qdrant |
| File path inconsistency (OSS vs local) | Medium | Low | Store both `video_path` (canonical) and `oss_url` (explicit) |

## Testing Strategy

### Unit Tests
- `VectorExportService.export_from_files()` with local paths
- `VectorExportService.export_from_files()` with OSS URLs
- Config migration logic

### Integration Tests
- End-to-end: Translate → Manual export → Verify Qdrant metadata
- End-to-end: Translate with auto-export enabled → Verify Qdrant metadata
- OSS upload → Vector export → Verify OSS URL in metadata

### Manual Testing
- UI workflow: Select files → Upload → Verify in Summary Library
- Batch upload: Multiple videos → Verify all uploaded
- Error cases: Invalid SRT, missing video, OSS failure

## Performance Considerations
- **OSS upload**: Can be slow for large videos (100MB+). Show progress bar.
- **Embedding generation**: Slow for long videos. Show progress + ETA.
- **Batch export**: Process sequentially to avoid overwhelming LLM API rate limits.

## Security Considerations
- OSS credentials stored encrypted (already handled by `oss_config.py`)
- Vector DB API keys stored encrypted (already handled)
- No new security surface introduced
