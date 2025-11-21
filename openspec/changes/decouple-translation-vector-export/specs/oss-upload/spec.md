## ADDED Requirements

### Requirement: OSS Integration with Vector Export
The system SHALL support uploading video files to OSS as part of vector database export workflow.

#### Scenario: Upload video to OSS before vector export
- **WHEN** user enables "Upload video to OSS" checkbox in Vector Export Manager
- **AND** clicks "Export to Vector Database"
- **THEN** call `OSSUploader.upload_file()` with video file path
- **AND** show progress bar: "Uploading to OSS... (X%)"
- **AND** on success, receive OSS URL: "https://bucket.oss.com/videos/2025-11-21/abc_video.mp4"
- **AND** use OSS URL as `video_path` in Qdrant metadata

#### Scenario: OSS upload fails during export
- **WHEN** OSS upload is attempted during vector export
- **AND** upload fails (network error, quota exceeded, etc.)
- **THEN** show error notification: "OSS upload failed: [error]. Continue with local path?"
- **AND** provide options: [Retry] [Use Local Path] [Cancel]
- **IF** user selects "Use Local Path", proceed with local file path

#### Scenario: OSS upload with retry
- **WHEN** OSS upload fails
- **AND** user selects "Retry"
- **THEN** retry upload up to 3 times (configurable)
- **AND** show retry attempt: "Retrying upload (2/3)..."
- **AND** on final failure, offer "Use Local Path" or "Cancel"

### Requirement: OSS URL Generation
The system SHALL generate consistent OSS URLs following configured path structure.

#### Scenario: Generate OSS object key
- **WHEN** uploading video to OSS
- **THEN** generate object key in format: `{path_prefix}/{date}/{uuid}_{filename}`
- **EXAMPLE**: "videos/2025-11-21/abc123_output_translated.mp4"
- **AND** ensure uniqueness with UUID prefix
- **AND** preserve original filename for clarity

#### Scenario: Generate public access URL
- **WHEN** OSS upload succeeds
- **THEN** construct public URL based on provider:
  - Aliyun OSS: "https://{bucket}.{endpoint}/{object_key}"
  - AWS S3: "https://{bucket}.s3.{region}.amazonaws.com/{object_key}"
  - MinIO: "http(s)://{endpoint}/{bucket}/{object_key}"
- **AND** use custom domain if configured: "{custom_domain}/{object_key}"
- **AND** return URL in `ExportResult.oss_url`
