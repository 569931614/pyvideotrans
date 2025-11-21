## ADDED Requirements

### Requirement: Manual Vector Database Export UI
The system SHALL provide a dedicated UI for manually uploading translated videos to vector database.

#### Scenario: Open Vector Export Manager
- **WHEN** user clicks "Summary Library" → "Upload to Vector Database" menu item
- **THEN** open Vector Export Manager dialog
- **AND** show file selection interface for video + SRT pairs

#### Scenario: Select video and SRT files for export
- **WHEN** user clicks "Add Files" button in Vector Export Manager
- **THEN** open file browser for selecting video file
- **AND** auto-detect corresponding SRT file (same name, .srt extension)
- **AND** if SRT found, add video+SRT pair to export list
- **AND** if SRT not found, show error: "SRT file not found for selected video"

#### Scenario: Preview metadata before export
- **WHEN** user has selected video+SRT files
- **THEN** parse SRT to extract metadata: language, duration, chunk count
- **AND** display preview: "video1.mp4 (zh-cn, 120 chunks, 5.2MB)"
- **AND** allow user to review before export

#### Scenario: Export to vector database without OSS upload
- **WHEN** user clicks "Export to Vector Database" button
- **AND** "Upload video to OSS" checkbox is NOT checked
- **THEN** call `VectorExportService.export_from_files()` with local video path
- **AND** show progress bar: "Generating embeddings... (X/Y chunks)"
- **AND** show progress bar: "Uploading to Qdrant..."
- **AND** on success, show notification: "Exported 2 videos to vector database"
- **AND** close dialog

#### Scenario: Export with OSS upload
- **WHEN** user clicks "Export to Vector Database" button
- **AND** "Upload video to OSS" checkbox IS checked
- **THEN** first upload video file to OSS
- **AND** show progress bar: "Uploading to OSS... (X%)"
- **AND** then call `VectorExportService.export_from_files()` with OSS URL
- **AND** show progress bar: "Generating embeddings... (X/Y chunks)"
- **AND** show progress bar: "Uploading to Qdrant..."
- **AND** on success, show notification: "Uploaded to OSS and exported to vector database"

#### Scenario: Batch export multiple videos
- **WHEN** user selects multiple video+SRT pairs
- **THEN** process each pair sequentially
- **AND** show overall progress: "Exporting video 2/5..."
- **AND** continue on individual failures (non-fatal)
- **AND** show summary: "Exported 4/5 videos. 1 failed."

#### Scenario: Detect duplicate video
- **WHEN** user attempts to export video
- **AND** video_id (SHA-256 hash) already exists in Qdrant
- **THEN** show warning: "This video already exists in vector database. Overwrite?"
- **AND** provide options: [Skip] [Overwrite] [Cancel]
- **IF** user selects "Overwrite", proceed with upload
- **IF** user selects "Skip", skip this video and continue to next

### Requirement: Vector Export Service API
The system SHALL provide a centralized service for vector database export, supporting both automatic and manual workflows.

#### Scenario: Export from translation task (automatic)
- **WHEN** `VectorExportService.export_from_task()` is called with task config
- **THEN** extract video path, SRT path, language from task config
- **AND** call existing `export_to_qdrant()` function
- **AND** store local file path in Qdrant metadata
- **AND** return `ExportResult` with success status

#### Scenario: Export from files (manual)
- **WHEN** `VectorExportService.export_from_files()` is called with video file, SRT file, and export config
- **THEN** validate video file exists and is readable
- **AND** validate SRT file exists and is readable
- **AND** if `upload_to_oss=True`, first upload video to OSS using `OSSUploader`
- **AND** call existing `export_to_qdrant()` function
- **AND** store OSS URL (if uploaded) or local path in Qdrant metadata
- **AND** return `ExportResult` with success status

#### Scenario: Batch export with progress callbacks
- **WHEN** `VectorExportService.batch_export()` is called with list of export items
- **THEN** iterate through items sequentially
- **AND** call `export_from_files()` for each item
- **AND** invoke progress callback after each item: `callback(current_index, total_count)`
- **AND** continue on individual failures (collect errors)
- **AND** return list of `ExportResult` for all items

## MODIFIED Requirements

### Requirement: Vector Database Metadata Schema
The system SHALL store video metadata in Qdrant including file location (local or OSS URL).

#### Scenario: Store metadata with local file path
- **WHEN** exporting video without OSS upload
- **THEN** store metadata with:
  - `video_path`: local file path (e.g., "F:/videos/output.mp4")
  - `source_type`: "pyvideotrans"
  - `oss_url`: null

#### Scenario: Store metadata with OSS URL
- **WHEN** exporting video after OSS upload
- **THEN** store metadata with:
  - `video_path`: OSS URL (e.g., "https://bucket.oss.com/videos/2025-11-21/abc_video.mp4")
  - `source_type`: "pyvideotrans_oss"
  - `oss_url`: OSS URL (explicit field)
  - `upload_timestamp`: Unix timestamp of upload

#### Scenario: Store folder assignment
- **WHEN** user selects folder during manual export
- **THEN** store metadata with:
  - `folder_id`: folder UUID
  - `folder`: folder name (for display)
